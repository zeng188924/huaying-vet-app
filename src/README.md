# src / 核心源码包

本目录包含华英兽医宝（专家版）的全部核心 Python 源码，按功能划分为 `core`、`admin`、`utils` 三个子包。

## 子包说明

### `core/` 业务引擎

| 文件 | 职责 |
| --- | --- |
| `drug_recommendation_system_full.py` | 兽药智能推荐系统：产品数据加载、相似度匹配、组合推荐、配伍禁忌检测 |
| `diagnosis_engine.py` | 症状诊断引擎、引导式问诊、用药安全分级 |
| `disease_knowledge.py` | 疾病知识库：症状、病原、防治原则、常用药物 |
| `drug_compatibility.py` | 药物配伍禁忌规则库与检测器 |
| `environment_adjustment.py` | 基于病症与棚舍环境生成环境调整建议 |
| `key_matters.py` | 兽医诊疗关键事项读取与结构化解析 |
| `egg_laying_banned_drugs_checker.py` | 蛋鸡产蛋期禁用药物拦截检查 |

### `admin/` 数据管理与内容提取

| 文件 | 职责 |
| --- | --- |
| `db_admin.py` | 产品数据库 CRUD、多媒体上传、配伍校验、Streamlit 管理界面 |
| `content_extractor.py` | 图片 OCR、PDF 文本、语音转文字及智能字段解析 |

### `utils/` 通用工具

| 文件 | 职责 |
| --- | --- |
| `data_manager.py` | 养殖户/棚舍档案的增删改查与 JSON 持久化 |
| `encryption.py` | 身份证/手机号哈希、Fernet 对称加密与密钥管理 |

## 导入约定

入口文件（`app.py`、`app_mobile.py`、`pages/*.py`）启动时会将 `src` 及其子目录加入 `sys.path`，因此历史模块导入方式（如 `from drug_compatibility import ...`、`from utils.data_manager import ...`）继续生效。
