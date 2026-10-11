"""项目配置：路径、外部 API 端点、超时与缓存 TTL。

可选配置通过项目根目录 .env 提供（见 .env.example），例如 OncoKB token。
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------- 路径
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = PROJECT_ROOT / "reports"
for _d in (DATA_DIR, CACHE_DIR, REPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- 外部 API
OPEN_TARGETS_GRAPHQL = "https://api.platform.opentargets.org/api/v4/graphql"
GWAS_CATALOG_V2 = "https://api.gwas.scientific-data.io/api/v2"
HUMAN_PROTEIN_ATLAS_TSV = (
    "https://www.proteinatlas.org/download/normal_tissue.tsv.zip"
)
STRING_API = "https://string-db.org/api"
CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
UNIPROT_API = "https://rest.uniprot.org/uniprotkb/search"
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
OPENFDA_DRUG_LABEL = "https://api.fda.gov/drug/label.json"
ONCOKB_API = "https://www.oncokb.org/api/v1"

ONCOKB_TOKEN = os.getenv("ONCOKB_TOKEN", "").strip()

# ---------------------------------------------------------------- 请求行为
REQUEST_TIMEOUT = 30.0          # 单个外部请求超时（秒）
MAX_RETRIES = 2                 # 网络错误重试次数
CACHE_TTL = 7 * 24 * 3600       # 缓存有效期：7 天
USER_AGENT = "target-five-questions/0.1 (research use; https://github.com/your-name/target-five-questions)"

# 五问定义（标题 + 问题原文，与 rules.yaml 的 key 对应）
FIVE_QUESTIONS = [
    {"key": "target", "title": "正确的靶点", "question": "它和疾病之间有没有扎实的因果证据？"},
    {"key": "tissue", "title": "正确的组织", "question": "药物能不能到达、并在正确的组织里起作用？"},
    {"key": "safety", "title": "正确的安全性", "question": "打这个靶点会不会出事？"},
    {"key": "patient", "title": "正确的患者", "question": "你能不能识别出“对的那群病人”？"},
    {"key": "commercial", "title": "正确的商业", "question": "值不值得做？"},
]
