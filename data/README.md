# data / 数据目录

本目录存放华英兽医宝（专家版）运行所需的全部数据文件，按用途分为档案、产品、配置三类。

## 子目录说明

### `profiles/` 档案数据

- `farmer_profiles.json`：养殖户档案（运行时生成）。
- `shed_profiles.json`：棚舍档案（运行时生成）。

### `products/` 产品数据

- `huaying_products_full.json`：清洗合并后的完整产品库（推荐系统主数据源）。
- `huaying_products.json`：早期版本产品数据（保留备份）。
- `产品信息_华英_已标注.json`：华英产品标注数据。

### `config/` 运行时配置

- `encryption_key.key`：Fernet 加密密钥（运行时自动生成，已加入 `.gitignore`，请勿提交）。

### `uploaded_media/` 上传多媒体

- 数据库管理中上传的图片、视频、文档等（运行时生成，已加入 `.gitignore`）。

## 维护建议

- 产品主数据更新时，优先替换 `products/huaying_products_full.json`。
- 档案数据为运行时生成，部署前可清空或保留示例数据。
- 敏感配置文件与上传文件不应纳入版本控制。
