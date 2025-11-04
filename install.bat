@echo off
chcp 65001 >nul
echo ========================================
echo   智能记账客户端 - 安装脚本
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查pip是否可用
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip不可用，请检查Python安装
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

:: 安装依赖
echo 正在安装依赖...
pip install flask requests >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装成功

:: 创建桌面快捷方式（可选）
set /p create_shortcut="是否创建桌面快捷方式? (y/n): "
if /i "%create_shortcut%"=="y" (
    echo 创建桌面快捷方式...
    copy "智能记账客户端.exe" "%userprofile%\Desktop\智能记账客户端.exe" >nul 2>&1
    echo ✅ 快捷方式创建成功
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 使用方法：
echo 1. 双击运行"智能记账客户端.exe"
echo 2. 系统会自动打开浏览器访问应用
echo 3. 使用测试账号: testuser / test123
echo.
echo 按任意键退出...
pause >nul
