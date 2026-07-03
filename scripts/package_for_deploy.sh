#!/bin/bash
# 华英兽医宝（专家版）- 本地打包脚本
# 用法：在 Windows 上可通过 Git Bash / WSL 运行，生成 deploy.tar.gz 后上传到服务器

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_NAME="huaying-vet-app-deploy.tar.gz"
OUTPUT_PATH="$PROJECT_ROOT/$PACKAGE_NAME"

echo "===== 开始打包项目 ====="
cd "$PROJECT_ROOT"

# 排除不需要部署的文件/目录
tar -czf "$OUTPUT_PATH" \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='deploy.tar.gz' \
    --exclude='huaying-vet-app-deploy.tar.gz' \
    --exclude='.mplconfig' \
    --exclude='*.log' \
    .

echo "===== 打包完成 ====="
echo "部署包路径: $OUTPUT_PATH"
echo ""
echo "下一步："
echo "1. 将 $PACKAGE_NAME 上传到服务器 /root 目录"
echo "2. 在服务器上执行："
echo "   mkdir -p /opt/huaying-vet-app"
echo "   tar -xzf /root/$PACKAGE_NAME -C /opt/huaying-vet-app"
echo "   bash /opt/huaying-vet-app/docker/deploy_server.sh"
