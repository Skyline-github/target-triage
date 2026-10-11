# Target Triage — Five Questions Before Project Initiation

**Enter a target gene and an indication; get an evidence-based, red/yellow/green risk-screened report answering the five questions that must be asked before a drug-discovery program starts.**

The framework follows AstraZeneca's 5R philosophy (Cook et al., *Nature Reviews Drug Discovery*, 2014): the top cause of pipeline failure in their 2005–2010 retrospective was not toxicity but lack of efficacy — traceable to insufficient confidence in target–disease linkage from the very beginning. The five dimensions multiply: what you need to find at initiation is not the highest-scoring dimension, but the one that will veto the project.

| Question | Automated evidence sources |
|---|---|
| ① Right **target** (causal evidence) | Open Targets Platform, GWAS Catalog |
| ② Right **tissue** (expression & delivery) | Human Protein Atlas, UniProt, STRING |
| ③ Right **safety** | OT mouse knockout lethality, LOF constraint (gnomAD), PharmGKB/ToxCast liabilities, ChEMBL approved drugs |
| ④ Right **patient** | openFDA drug labels, OncoKB (optional token) |
| ⑤ Right **commercial** | ClinicalTrials.gov (trial counts / termination reasons), openFDA |

> **Important**: red/yellow/green signals are threshold-rule screens, not conclusions. Red items go to a "risk signals — human judgment required" list, yellow to "verify further"; the final call always belongs to the assessor. All thresholds live in `app/engine/rules.yaml` and are editable.

## Quickstart

```bash
conda create -n tav python=3.12 -y && conda activate tav
pip install -r requirements.txt
uvicorn app.main:app --reload        # open http://127.0.0.1:8000
```

First assessment auto-downloads the Human Protein Atlas v22 tissue file (~6 MB compressed), then reuses it offline. All queries are cached locally for 7 days (`data/cache/`).

```bash
# HTML UI: POST a form, or use the JSON API
curl -X POST http://127.0.0.1:8000/assess -d "gene=EGFR&indication=non-small cell lung carcinoma"

# offline unit tests + live API smoke test
python -m pytest tests/test_offline.py -q
python tests/smoke_api.py EGFR
```

Optional: request a free academic [OncoKB](https://www.oncokb.org) token and put `ONCOKB_TOKEN=xxx` in `.env` to enable the oncology companion-diagnostics module.

## Output

Each assessment archives four deliverables under `reports/` (two real examples committed in `reports_sample/`: **MAPT**/Alzheimer's — "insufficient information" verdict, and **GLCE**/pancreatic cancer — "danger signals" verdict):

- **HTML report** — overview card (five-question radar + risk checklist) → per-question cards with Chart.js figures (disease association bars, tissue expression profile, safety-event distribution, trial-status ring), collapsible raw data
- **Markdown / Excel / JSON** archives for notes, team review and downstream analysis

Paid sources (Clarivate, Cortellis, Evaluate Pharma) are deliberately not automated; the report renders them as manual-check checklists with direct links.

## Structure

```
app/
├── main.py                 # FastAPI routes
├── config.py               # endpoints / timeouts / cache config
├── models.py               # report data models (Evidence / QuestionReport / AssessmentReport)
├── cache.py, jobs.py       # JSON-file cache, assessment jobs
├── services/               # 9 data-source adapters (opentargets / gwas / protein_atlas /
│                           #  uniprot / stringdb / chembl / clinicaltrials / openfda / oncokb)
├── engine/
│   ├── five_questions.py   # orchestrator (asyncio-concurrent fetching)
│   └── rules.yaml          # red/yellow/green thresholds — edit here to retune
└── reporting/export.py     # HTML / Markdown / Excel export
```

中文说明见 [README.zh-CN.md](README.zh-CN.md)。

## License

MIT — see [LICENSE](LICENSE).

## Author

Shengjie Wu — Ph.D. in medicinal chemistry (SIMM, CAS). Self-directed AIDD project; feedback and issues welcome.
