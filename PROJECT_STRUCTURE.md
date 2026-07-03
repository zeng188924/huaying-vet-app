# 华英兽医宝（专家版）项目结构说明

本文档说明整理后的项目目录结构、各文件夹用途以及关键文件定位，便于开发、维护和后续扩展。

## 目录总览

```
华英用药指南/
├── app.py                      # Streamlit 桌面端主入口
├── app_mobile.py               # Streamlit 移动端主入口
├── pages/                      # Streamlit 多页面
│   ├── 01_farmer_profile.py    # 养殖户档案管理页
│   ├── 02_shed_management.py   # 棚舍管理页
│   └── 03_drug_recommendation.py # 智能用药推荐页
├── src/                        # 核心源代码包
│   ├── core/                   # 业务引擎（推荐、诊断、知识库等）
│   ├── admin/                  # 数据库管理与内容提取
│   └── utils/                  # 通用工具（数据管理、加密）
├── data/                       # 数据文件
│   ├── profiles/               # 养殖户与棚舍档案
│   ├── products/               # 产品数据（JSON / Excel 来源）
│   └── config/                 # 运行时配置与密钥
├── docs/                       # 项目文档与说明
├── assets/                     # 静态资源
│   ├── images/                 # 图片
│   └── data_sources/           # 原始数据源表格
├── docker/                     # 容器化配置
├── scripts/                    # 工具脚本（预留）
├── tests/                      # 测试目录（预留）
├── requirements.txt            # Python 依赖
├── packages.txt                # 系统级依赖
├── .gitignore                  # Git 忽略规则
├── .streamlit/                 # Streamlit 配置文件
└── PROJECT_STRUCTURE.md        # 本文件
```

## 关键目录与文件说明

### 入口与页面

- `app.py`：桌面端主程序，提供首页导航与三大功能模块入口。
- `app_mobile.py`：移动端适配版本，采用居中布局与折叠侧边栏。
- `pages/`：Streamlit 多页面目录，文件名前缀数字控制页面排序。

### 核心源码 `src/`

| 子目录 | 用途 |
| --- | --- |
| `src/core/` | 业务核心引擎：智能推荐、诊断引擎、疾病知识库、配伍禁忌检测、环境调整建议、关键事项、产蛋期禁用药物检查 |
| `src/admin/` | 产品数据库管理后台与 OCR/文本/语音内容提取器 |
| `src/utils/` | 通用工具：档案数据持久化、身份证/手机号哈希、Fernet 加密 |

### 数据 `data/`

| 子目录 | 用途 |
| --- | --- |
| `data/profiles/` | 运行时生成的养殖户档案与棚舍档案 |
| `data/products/` | 产品信息库（完整数据、清洗后数据、标注数据） |
| `data/config/` | 运行时生成的加密密钥等配置 |
| `data/uploaded_media/` | 数据库管理中上传的多媒体文件（运行时生成，已加入 .gitignore） |

### 文档与资源

- `docs/`：使用说明、部署指南、数据清理报告、业务规则文档等。
- `assets/images/`：封面、示意图等图片资源。
- `assets/data_sources/`：原始 Excel 数据源，用于数据初始化或回退加载。

### 部署

- `docker/Dockerfile`：基于 Python 3.10 的容器镜像构建文件。
- `docker/docker-compose.yml`：服务编排文件，构建上下文指向项目根目录。

## 模块导入说明

由于核心代码已集中到 `src/` 包下，各入口文件（`app.py`、`app_mobile.py`、`pages/*.py`）在启动时会自动将 `src` 及其子目录加入 `sys.path`，确保历史导入语句（如 `from drug_compatibility import ...`、`from utils.data_manager import ...`）继续可用，无需修改业务逻辑。

## 启动方式

```bash
# 桌面端
streamlit run app.py

# 移动端
streamlit run app_mobile.py

# Docker
cd docker
docker-compose up --build
```

## 注意事项

- 所有原始代码的业务逻辑未做改动，仅调整文件位置与必要的路径引用。
- 整理过程中发现 `华英兽医宝推广方案.md` 未能定位到有效文件，请用户核对是否需要补充。
