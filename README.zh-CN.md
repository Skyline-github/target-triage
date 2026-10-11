# 靶点立项五问 · Target Five Questions

> English introduction: see [README.md](README.md).

> 输入一个靶点基因，自动调取开源数据库证据，回答药物研发立项前必须问的五个问题——
> 并用图表把每类证据摊开，标出哪个维度可能成为短板。

框架源自 AstraZeneca 的 5R 体系（Cook et al., *Nature Reviews Drug Discovery*, 2014）：
复盘 2005–2010 年小分子管线发现，项目失败的头号原因不是毒性，而是疗效不足；
根因几乎都指向"靶点与疾病的关联从一开始就没建立足够信心"。

五个维度是**乘法**关系：立项阶段真正要找的不是"哪个维度得分最高"，
而是"哪个维度会成为短板"。

**重要**：红/黄/绿是阈值规则自动生成的**筛查信号**，不是结论——
红色项列入"风险信号（需人工判断）"，黄色项列入"建议进一步核查"，
最终判断权始终在评估者。所有阈值集中在 `app/engine/rules.yaml`，可自行调整。

## 五问与数据源

| 五问 | 自动化数据源 | 手动核查项 |
|---|---|---|
| ① 正确的靶点（因果证据） | Open Targets Platform（关联分数/遗传学分型）、GWAS Catalog | DisGeNET、TTD |
| ② 正确的组织（表达与递送） | Human Protein Atlas（组织特异/分布 + 44 组织 IHC 表）、UniProt | KEGG、Reactome、STRING |
| ③ 正确的安全性 | OT 小鼠敲除致死性、isEssential、LOF 约束 z 分数（gnomAD）、Safety liabilities（PharmGKB/ToxCast）、ChEMBL 同靶点上市药 | gnomAD 携带者表型、家族级安全记录 |
| ④ 正确的患者 | openFDA 药物标签、OncoKB（可选，需 token） | FDA 伴随诊断清单、PubMed 患病率检索、Clarivate |
| ⑤ 正确的商业 | ClinicalTrials.gov（试验数/终止原因）、openFDA | FTO 专利分析、Cortellis、Evaluate Pharma |

付费/需注册数据源不自动化，报告以"手动核查清单 + 直达链接"呈现。

## 快速开始

```bash
# 1) 创建环境（conda 或 venv 均可，Python ≥ 3.11）
conda create -n tav python=3.12 -y
conda activate tav

# 2) 安装依赖
pip install -r requirements.txt

# 3) 启动
uvicorn app.main:app --reload
# 打开 http://127.0.0.1:8000
```

首次评估会自动下载 Human Protein Atlas v22 组织表达文件（约 6MB 压缩包），
之后离线复用。全部查询有 7 天本地缓存（`data/cache/`）。

**可选**：申请 [OncoKB](https://www.oncokb.org) 免费学术 token 后，
在项目根目录建 `.env` 写入 `ONCOKB_TOKEN=xxx`，即可启用肿瘤伴随诊断模块。

### 离线测试与冒烟

```bash
python -m pytest tests/test_offline.py -q   # 离线单元测试
python tests/smoke_api.py EGFR              # 真实 API 冒烟（需联网）
```

### API 用法

```bash
# HTML 界面：POST 表单即可；也可走 JSON 接口（见 app/main.py）
curl -X POST http://127.0.0.1:8000/assess -d "gene=EGFR&indication=non-small cell lung carcinoma"
```

## 输出

每次评估生成四份归档（`reports/<id>`）：

- **网页报告**：概览卡（五问雷达图 + 风险信号/建议核查清单）→ 五问导航卡片 →
  每类证据一张卡片，配 Chart.js 图表（关联疾病条形图、组织表达谱、
  安全事件分布、试验状态环形图等），原始数据可折叠查看
- **Markdown 存档**：可直接贴进笔记/仓库
- **Excel**：自动证据表 + 手动核查清单 + 风险信号/建议核查表
- **JSON**：完整结构化数据（含图表配置），便于二次分析

## 项目结构

```
app/
├── main.py                 # FastAPI 路由
├── config.py               # 端点/超时/缓存配置
├── models.py               # 报告数据模型（Evidence / QuestionReport / AssessmentReport）
├── cache.py, jobs.py       # JSON 文件缓存、评估任务
├── services/               # 9 个数据源适配器（opentargets / gwas / protein_atlas /
│   │                       #  uniprot / stringdb / chembl / clinicaltrials / openfda / oncokb）
├── engine/
│   ├── five_questions.py   # 五问编排器（asyncio 并发取数）
│   └── rules.yaml          # 红/黄/绿阈值 —— 想调判据改这里
└── reporting/export.py     # HTML / Markdown / Excel 导出
```

## 调整评分阈值

所有判据集中在 `app/engine/rules.yaml`，例如：

```yaml
safety:
  lof_z_strong: 3.09     # LOF 约束 z 分数 ≥ 此值 → 红灯（治疗窗可能极窄）
commercial:
  trials_crowded: 50     # 临床试验数 > 此值 → 黄灯（赛道拥挤）
```

## 已知限制

- GWAS Catalog 使用 V2 API（`api.gwas.scientific-data.io`），旧 REST 已弃用；
  个别网络环境解析该域名失败时会自动降级为手动核查链接（Q1 的遗传学证据
  主要来自 Open Targets 的 `genetic_association` 分型，不受影响）。
- LOF 约束使用 Open Targets 转出的 gnomAD z 分数（z ≥ 3.09 视为经典高约束），
  未直接接 gnomAD GraphQL；需要更细粒度请到 gnomAD 基因页人工确认。
- 小鼠敲除致死性判定基于 MP 表型标签的关键词匹配（`*lethal*`），
  是筛查信号而非结论。
- 评估结果**仅供研究参考**，不构成任何立项、临床或投资建议。

## 致谢

数据与框架来源：Open Targets Platform、GWAS Catalog（NHGRI-EBI）、Human Protein Atlas、
UniProt、STRING、ChEMBL（EBI）、ClinicalTrials.gov（NIH）、openFDA、OncoKB；
立项五问方法论：AstraZeneca 5R（Cook et al., NRDD 2014）及小红书「药言说 · 药物设计」
的科普梳理。使用各库时请遵守其各自的引用要求与许可条款。

## License

MIT
