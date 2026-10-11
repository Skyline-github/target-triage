"""报告导出：HTML 存档、Markdown 存档、Excel 证据表。"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import REPORTS_DIR
from ..models import AssessmentReport, Evidence

STATUS_BADGE = {"green": "🟢 良好", "yellow": "🟡 需注意",
                "red": "🔴 危险信号", "unknown": "⚪ 信息不足"}


def save_report(report: AssessmentReport) -> dict:
    """保存三种格式的归档，返回各文件路径。"""
    rid = report.id
    out = {
        "json": REPORTS_DIR / f"{rid}.json",
        "html": REPORTS_DIR / f"{rid}.html",
        "markdown": REPORTS_DIR / f"{rid}.md",
        "excel": REPORTS_DIR / f"{rid}.xlsx",
    }
    out["json"].write_text(report.model_dump_json(indent=2))
    out["html"].write_text(render_html(report))
    out["markdown"].write_text(render_markdown(report))
    export_excel(report, out["excel"])
    return {k: str(v) for k, v in out.items()}


# ---------------------------------------------------------------- HTML
def render_html(report: AssessmentReport) -> str:
    from jinja2 import Environment, FileSystemLoader

    from .radar import radar_chart_config

    env = Environment(loader=FileSystemLoader(
        str(Path(__file__).resolve().parent.parent / "templates")), autoescape=True)
    tpl = env.get_template("report_static.html")
    return tpl.render(r=report, badge=STATUS_BADGE,
                      radar_cfg=radar_chart_config(report))


# ---------------------------------------------------------------- Markdown
def _ev_md(ev: Evidence) -> list[str]:
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴", "unknown": "⚪"}[ev.status]
    lines = [f"### {icon} {ev.source} · {ev.check}", ""]
    lines.append(ev.summary)
    if ev.detail:
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(ev.detail, ensure_ascii=False, indent=2)[:2000])
        lines.append("```")
    if ev.links:
        lines.append("")
        lines.append(" · ".join(f"[{l.label}]({l.url})" for l in ev.links))
    lines.append("")
    return lines


def render_markdown(report: AssessmentReport) -> str:
    md = [
        f"# 靶点立项五问评估：{report.gene_symbol}",
        "",
        f"- **靶点全名**：{report.gene_name or '—'}（Ensembl: {report.ensembl_id}, "
        f"UniProt: {report.uniprot_id or '—'}）",
        f"- **限定适应症**：{report.indication or '不限'}",
        f"- **评估时间**：{report.created_at}",
        f"- **总体状态**：{STATUS_BADGE[report.overall_status]}",
        "",
    ]
    if report.risk_flags:
        md += ["## 🚩 风险信号（数据筛查提示，需人工判断，不等于结论）", ""]
        md += [f"- {v}" for v in report.risk_flags] + [""]
    if report.watch_flags:
        md += ["## 👀 建议进一步核查", ""]
        md += [f"- {v}" for v in report.watch_flags] + [""]
    md += ["> 五个维度是乘法关系：立项阶段真正要找的不是哪个维度得分最高，"
           "而是哪个维度会成为短板。红/黄/绿为阈值规则自动生成的筛查信号，不是结论。", ""]
    for q in report.questions:
        md += [f"## {q.title}：{q.question}", ""]
        for ev in q.evidences:
            md += _ev_md(ev)
        if q.manual_checklist:
            md += ["## 手动核查清单", ""]
            for ev in q.manual_checklist:
                md += [f"- **{ev.source} · {ev.check}**：{ev.summary}  "
                       + " · ".join(f"[{l.label}]({l.url})" for l in ev.links)]
            md.append("")
    md += ["---", "*本报告由开源数据自动生成，仅供研究参考，不构成任何投资或立项建议。*"]
    return "\n".join(md)


# ---------------------------------------------------------------- Excel
def export_excel(report: AssessmentReport, path: Path) -> None:
    import pandas as pd

    auto_rows: list[dict] = []
    manual_rows: list[dict] = []
    for q in report.questions:
        for ev in q.evidences:
            auto_rows.append({
                "五问": q.title, "来源": ev.source, "检查点": ev.check,
                "状态": STATUS_BADGE[ev.status], "结论": ev.summary,
                "详情(JSON)": json.dumps(ev.detail, ensure_ascii=False)[:1000] if ev.detail else "",
                "链接": " ; ".join(l.url for l in ev.links),
            })
        for ev in q.manual_checklist:
            manual_rows.append({
                "五问": q.title, "来源": ev.source, "检查点": ev.check,
                "说明": ev.summary,
                "链接": " ; ".join(l.url for l in ev.links),
            })
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(auto_rows).to_excel(writer, sheet_name="自动证据", index=False)
        if manual_rows:
            pd.DataFrame(manual_rows).to_excel(writer, sheet_name="手动核查清单", index=False)
        if report.risk_flags:
            pd.DataFrame({"风险信号（需人工判断）": report.risk_flags}).to_excel(
                writer, sheet_name="风险信号", index=False)
        if report.watch_flags:
            pd.DataFrame({"建议进一步核查": report.watch_flags}).to_excel(
                writer, sheet_name="建议核查", index=False)
