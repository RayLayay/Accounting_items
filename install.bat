@echo off
chcp 65001 >nul
title 智能记账客户端安装程序

echo ========================================
echo   智能记账客户端 - 安装程序
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境正常

echo.
echo [2/4] 检查Flask依赖...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 正在安装Flask依赖...
    pip install flask
    if %errorlevel% neq 0 (
        echo ❌ Flask安装失败，请手动运行: pip install flask
        pause
        exit /b 1
    )
    echo ✅ Flask安装成功
) else (
    echo ✅ Flask依赖已安装
)

echo.
echo [3/4] 检查数据库文件...
if not exist "finance_system.db" (
    echo ❌ 数据库文件不存在，请确保所有文件完整
    pause
    exit /b 1
)
echo ✅ 数据库文件正常

echo.
echo [4/4] 启动智能记账客户端...
echo.
echo 🚀 正在启动客户端...
echo 📊 访问地址: http://127.0.0.1:5000
echo 👤 测试账号: testuser / test123
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python start_client.py

pause
