#!/bin/bash

APP_NAME="huaying-vet-app"
APP_DIR="/opt/huaying-vet-app"
APP_PORT=8501

echo "=========================================="
echo "  华英兽药智能推荐系统 - 部署脚本"
echo "=========================================="
echo ""

if [ "$(id -u)" != "0" ]; then
    echo "⚠️  警告：建议使用 root 用户运行此脚本以获得完整权限"
    echo ""
fi

echo "📦 步骤1: 创建应用目录..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/data
echo "✅ 目录创建完成"
echo ""

echo "📦 步骤2: 复制应用文件..."
cp -r ./* $APP_DIR/
echo "✅ 文件复制完成"
echo ""

echo "📦 步骤3: 检查Python环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误：未找到Python，请先安装Python"
    exit 1
fi

echo "使用Python: $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

echo "📦 步骤4: 安装依赖..."
cd $APP_DIR
$PYTHON_CMD -m pip install --upgrade pip -q
$PYTHON_CMD -m pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成"
else
    echo "❌ 依赖安装失败，请检查网络连接"
    exit 1
fi
echo ""

echo "📦 步骤5: 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --add-port=$APP_PORT/tcp --permanent
    firewall-cmd --reload
    echo "✅ 防火墙配置完成（开放端口 $APP_PORT）"
elif command -v ufw &> /dev/null; then
    ufw allow $APP_PORT/tcp
    echo "✅ 防火墙配置完成（开放端口 $APP_PORT）"
else
    echo "⚠️  未检测到防火墙工具，请手动开放端口 $APP_PORT"
fi
echo ""

echo "📦 步骤6: 创建启动服务..."

cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=华英兽药智能推荐系统
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$PYTHON_CMD -m streamlit run app_mobile.py --server.port $APP_PORT --server.address 0.0.0.0
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 服务配置文件创建完成"
echo ""

echo "📦 步骤7: 启动服务..."
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl start $APP_NAME

if [ $? -eq 0 ]; then
    echo "✅ 服务启动成功"
else
    echo "❌ 服务启动失败，请检查日志"
    exit 1
fi
echo ""

echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "📱 访问地址: http://服务器IP:$APP_PORT"
echo ""
echo "🔧 常用命令:"
echo "  查看状态: systemctl status $APP_NAME"
echo "  停止服务: systemctl stop $APP_NAME"
echo "  启动服务: systemctl start $APP_NAME"
echo "  重启服务: systemctl restart $APP_NAME"
echo "  查看日志: journalctl -u $APP_NAME -f"