# docker / 容器化配置

本目录包含华英兽医宝（专家版）的 Docker 构建与编排配置。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `Dockerfile` | 基于 `python:3.10-slim` 构建运行镜像，安装 Tesseract、Poppler、FFmpeg、libgl1 等依赖 |
| `docker-compose.yml` | 服务编排，构建上下文指向项目根目录 |

## 使用方式

```bash
cd docker
docker-compose up --build
```

服务启动后访问 `http://localhost:8501`。

## 注意事项

- `docker-compose.yml` 中的 `context: ..` 表示以项目根目录作为构建上下文，因此 `Dockerfile` 中的 `COPY requirements.txt .` 与 `COPY . .` 均能正确找到根目录文件。
- 默认启动命令运行 `app_mobile.py`，如需运行桌面端可修改 `Dockerfile` 最后的 `CMD`。
