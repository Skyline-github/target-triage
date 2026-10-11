"""真实 API 冒烟测试（需要联网）：

    python tests/smoke_api.py [基因符号，默认 EGFR]

逐个验证数据源服务，再跑一次完整五问评估并导出报告到 reports/。
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engine.five_questions import assess
from app.models import STATUS_LABEL
from app.reporting.export import save_report
from app.services import (chembl, clinicaltrials, gwas, openfda,
                          opentargets as ot, protein_atlas, stringdb, uniprot)


async def main(symbol: str) -> None:
    print(f"== 解析靶点 {symbol}")
    resolved = await ot.search_target(symbol)
    assert resolved, f"Open Targets 未收录 {symbol}"
    ensembl = resolved["ensembl_id"]
    print("   ensembl:", ensembl)

    checks = [
        ("OT overview", ot.get_target_overview(ensembl)),
        ("OT associations", ot.get_associations(ensembl, 5)),
        ("OT safety", ot.get_safety(ensembl)),
        ("OT mouse KO", ot.get_mouse_knockout(ensembl)),
        ("UniProt", uniprot.get_protein(symbol)),
        ("STRING", stringdb.get_interactions(symbol, 5)),
        ("ChEMBL", chembl.get_drugs(symbol)),
        ("ClinicalTrials", clinicaltrials.get_trials(symbol)),
        ("openFDA", openfda.get_label_mentions(symbol)),
        ("GWAS Catalog", gwas.get_associations_for_gene(symbol)),
        ("HPA", protein_atlas.get_tissue_expression(symbol, ensembl)),
    ]
    for name, coro in checks:
        try:
            await asyncio.wait_for(coro, timeout=120)
            print(f"   [OK] {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"   [FAIL] {name}: {type(exc).__name__}: {str(exc)[:120]}")

    print(f"== 完整五问评估 {symbol}")
    report = await assess(symbol)
    print(f"   总体: {STATUS_LABEL[report.overall_status]}，"
          f"一票否决 {len(report.veto_flags)} 项")
    files = save_report(report)
    print("   导出:", json.dumps(files, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "EGFR"))
