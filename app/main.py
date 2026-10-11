"""FastAPI 入口：uvicorn app.main:app --reload"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import jobs
from .config import FIVE_QUESTIONS, PROJECT_ROOT, REPORTS_DIR
from .engine.five_questions import DATA_SOURCES
from .models import STATUS_LABEL
from .reporting.radar import radar_chart_config

app = FastAPI(title="靶点立项五问 — Target Five Questions", version="0.1.0")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "app" / "templates"))
templates.env.globals["badge"] = STATUS_LABEL


def _ctx(request: Request, **kw):
    kw["request"] = request
    kw.setdefault("badge", STATUS_LABEL)
    return kw


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html",
                                      _ctx(request, questions=FIVE_QUESTIONS))


@app.post("/assess", response_class=HTMLResponse)
async def assess(request: Request, gene: str = Form(...), indication: str = Form("")):
    job_id = uuid.uuid4().hex[:12]
    jobs.start_job(job_id, gene, indication)
    return templates.TemplateResponse(
        request, "_status.html", _ctx(request, job_id=job_id, gene=gene.upper()))


@app.get("/jobs/{job_id}/status", response_class=HTMLResponse)
async def job_status(request: Request, job_id: str):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(404, "任务不存在")
    if job.status == "done":
        return RedirectResponse(f"/report/{job.report_id}", status_code=303)
    if job.status == "error":
        return HTMLResponse(f'<div class="alert alert-danger">评估失败：{job.error}</div>')
    return templates.TemplateResponse(
        request, "_status.html", _ctx(request, job_id=job_id, gene=job.gene))


@app.get("/report/{report_id}.{ext}", response_class=FileResponse)
async def report_download(report_id: str, ext: str):
    path = REPORTS_DIR / f"{report_id}.{ext}"
    if not path.exists():
        raise HTTPException(404, "文件不存在")
    media = {"html": "text/html", "md": "text/markdown",
             "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             "json": "application/json"}.get(ext, "application/octet-stream")
    return FileResponse(path, media_type=media, filename=path.name)


@app.get("/report/{report_id}", response_class=HTMLResponse)
async def report_view(request: Request, report_id: str):
    report = jobs.load_report_from_disk(report_id)
    if report is None:
        raise HTTPException(404, "报告不存在")
    return templates.TemplateResponse(
        request, "report.html",
        _ctx(request, r=report, radar_cfg=radar_chart_config(report),
             rule_note="app/engine/rules.yaml"))


@app.get("/archive", response_class=HTMLResponse)
async def archive(request: Request):
    return templates.TemplateResponse(
        request, "archive.html", _ctx(request, items=jobs.archived_reports()))


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    uses = {
        "Open Targets Platform": "靶点-疾病关联、安全事件、遗传约束、小鼠敲除（主干）",
        "GWAS Catalog": "人类遗传学信号补充",
        "Human Protein Atlas": "44 种正常组织蛋白表达 + RNA 表达",
        "UniProt": "蛋白功能与亚细胞定位注释",
        "STRING": "蛋白-蛋白互作网络",
        "ChEMBL": "靶点药物、作用机制与研发阶段",
        "ClinicalTrials.gov": "竞争格局：试验数量、状态、终止原因",
        "openFDA": "药物标签中靶点/突变提及（上市产品线索）",
        "OncoKB（可选）": "伴随诊断与精准肿瘤学证据（需配置 ONCOKB_TOKEN）",
    }
    sources = [{**s, "use": uses.get(s["name"], "")} for s in DATA_SOURCES]
    return templates.TemplateResponse(request, "about.html", _ctx(request, sources=sources))
