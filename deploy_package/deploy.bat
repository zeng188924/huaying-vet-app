@echo off
chcp 65001 >nul
echo ==========================================
echo   华英兽药智能推荐系统 - Windows部署脚本
echo ==========================================
echo.

set APP_NAME=huaying-vet-app
set APP_DIR=C:\huaying-vet-app
set APP_PORT=8501

echo 📦 步骤1: 创建应用目录...
mkdir "%APP_DIR%" >nul 2>&1
mkdir "%APP_DIR%\data" >nul 2>&1
echo ✅ 目录创建完成
echo.

echo 📦 步骤2: 复制应用文件...
xcopy /E /Y /Q .\* "%APP_DIR%\"
echo ✅ 文件复制完成
echo.

echo 📦 步骤3: 检查Python环境...
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
    ) else (
        echo ❌ 错误：未找到Python，请先安装Python
        pause
        exit /b 1
    )
)

echo 使用Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

echo 📦 步骤4: 安装依赖...
cd /d "%APP_DIR%"
%PYTHON_CMD% -m pip install --upgrade pip -q
%PYTHON_CMD% -m pip install -r requirements.txt -q

if %errorlevel% equ 0 (
    echo ✅ 依赖安装完成
) else (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo.

echo 📦 步骤5: 启动应用...
echo.
echo ⚠️  应用将在后台运行，请不要关闭此窗口
echo.
echo 📱 访问地址: http://localhost:%APP_PORT%
echo.

%PYTHON_CMD% -m streamlit run app_mobile.py --server.port %APP_PORT% --server.address 0.0.0.0

pause