"""离线单元测试：模型聚合逻辑、缓存、报告导出、规则加载。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.cache import cache_get, cache_set
from app.engine.five_questions import rules
from app.models import (AssessmentReport, Evidence, GREEN, QuestionReport, RED,
                        UNKNOWN, YELLOW)
from app.reporting.export import render_markdown, save_report


def _question(key: str, status: str) -> QuestionReport:
    return QuestionReport(
        key=key, title=key, question="?",
        evidences=[Evidence(source="t", check="c", status=status, summary="s")])


def _report(q_statuses: list[str]) -> AssessmentReport:
    r = AssessmentReport(id="test0001", gene_symbol="TEST1")
    r.questions = [_question(f"q{i}", s) for i, s in enumerate(q_statuses)]
    r.finalize()
    return r


class TestAggregate:
    def test_any_red_is_red(self):
        q = _question("t", GREEN)
        q.evidences.append(Evidence(source="t", check="c", status=RED, summary=""))
        q.aggregate()
        assert q.status == RED

    def test_yellow_wins_over_green(self):
        q = _question("t", YELLOW)
        q.aggregate()
        assert q.status == YELLOW

    def test_all_green(self):
        q = _question("t", GREEN)
        q.aggregate()
        assert q.status == GREEN

    def test_unknown(self):
        q = _question("t", UNKNOWN)
        q.aggregate()
        assert q.status == UNKNOWN


class TestFinalize:
    def test_risk_flags_collect_red_evidence(self):
        r = _report([GREEN, GREEN, RED, GREEN, GREEN])
        assert r.overall_status == RED
        assert len(r.risk_flags) == 1
        assert "q2" in r.risk_flags[0]

    def test_watch_flags_collect_yellow(self):
        r = _report([GREEN, GREEN, YELLOW, GREEN, GREEN])
        assert r.overall_status == YELLOW
        assert r.risk_flags == []
        assert len(r.watch_flags) == 1

    def test_legacy_veto_json_loads(self):
        legacy = ('{"id": "abc", "gene_symbol": "X", "veto_flags": ["旧字段"]}'
                  )
        r = AssessmentReport.model_validate_json(legacy)
        assert r.risk_flags == ["旧字段"]

    def test_no_red_but_unknown(self):
        r = _report([GREEN, GREEN, UNKNOWN, GREEN, GREEN])
        assert r.overall_status == UNKNOWN
        assert r.risk_flags == []

    def test_all_green_is_green(self):
        r = _report([GREEN] * 5)
        assert r.overall_status == GREEN

    def test_radar_data(self):
        r = _report([GREEN, YELLOW, RED, UNKNOWN, GREEN])
        assert len(r.radar_data["values"]) == 5
        assert r.radar_data["values"][0] == 3
        assert r.radar_data["values"][2] == 1


class TestRules:
    def test_rules_load_with_expected_keys(self):
        r = rules()
        for key in ("target", "tissue", "safety", "commercial"):
            assert key in r
        assert "association_strong" in r["target"]
        assert "lof_z_strong" in r["safety"]
        assert "trials_crowded" in r["commercial"]


class TestCache:
    def test_roundtrip(self, tmp_path, monkeypatch):
        import app.cache as cache_mod
        monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(cache_mod, "_cache_path",
                            lambda s, k: tmp_path / f"{s}_{hash(k) & 0xffff}.json")
        cache_set("svc", "key", {"a": 1})
        assert cache_get("svc", "key") == {"a": 1}
        assert cache_get("svc", "missing") is None


class TestExport:
    def test_save_report_outputs(self, tmp_path, monkeypatch):
        import app.reporting.export as ex
        monkeypatch.setattr(ex, "REPORTS_DIR", tmp_path)
        r = _report([GREEN, YELLOW, RED, UNKNOWN, GREEN])
        files = save_report(r)
        for ext in ("json", "html", "markdown", "excel"):
            assert Path(files[ext]).exists()
        md = Path(files["markdown"]).read_text()
        assert "TEST1" in md
        assert "风险信号" in md
        assert "仅供研究参考" in md

    def test_markdown_contains_links(self):
        r = _report([GREEN] * 5)
        r.questions[0].evidences[0].links = []
        md = render_markdown(r)
        assert "靶点立项五问评估" in md
