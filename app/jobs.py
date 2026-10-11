"""评估任务管理：后台执行 + 状态查询。"""
from __future__ import annotations

import asyncio
import traceback
from dataclasses import dataclass, field

from .engine.five_questions import assess
from .models import AssessmentReport, STATUS_LABEL
from .reporting.export import save_report


@dataclass
class Job:
    id: str
    gene: str
    indication: str
    status: str = "running"            # running / done / error
    report_id: str | None = None
    error: str = ""
    report: AssessmentReport | None = None
    files: dict = field(default_factory=dict)


_JOBS: dict[str, Job] = {}


async def _run(job: Job) -> None:
    try:
        report = await assess(job.gene, job.indication)
        job.report = report
        job.files = save_report(report)
        job.report_id = report.id
        job.status = "done"
    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = f"{exc}"
        traceback.print_exc()


def start_job(job_id: str, gene: str, indication: str) -> Job:
    job = Job(id=job_id, gene=gene, indication=indication)
    _JOBS[job_id] = job
    asyncio.get_running_loop().create_task(_run(job))
    return job


def get_job(job_id: str) -> Job | None:
    return _JOBS.get(job_id)


def load_report_from_disk(report_id: str) -> AssessmentReport | None:
    """从归档 JSON 重建报告（重启后仍可访问历史评估）。"""
    from .config import REPORTS_DIR

    path = REPORTS_DIR / f"{report_id}.json"
    if not path.exists():
        return None
    return AssessmentReport.model_validate_json(path.read_text())


def archived_reports() -> list[dict]:
    from .config import REPORTS_DIR

    items = []
    for path in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        try:
            r = AssessmentReport.model_validate_json(path.read_text())
            items.append({"id": r.id, "gene_symbol": r.gene_symbol,
                          "indication": r.indication,
                          "overall_status": r.overall_status,
                          "status_label": STATUS_LABEL[r.overall_status],
                          "created_at": r.created_at})
        except Exception:  # noqa: BLE001
            continue
    return items
