@echo off
chcp 65001 >nul
title 智能记账客户端打包工具

echo ========================================
echo   智能记账客户端 - 打包工具
echo ========================================
echo.

set "PACKAGE_DIR=智能记账客户端分发包"

echo [1/5] 创建分发包目录...
if exist "%PACKAGE_DIR%" (
    echo ⚠️ 删除旧的分发包目录...
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"
if %errorlevel% neq 0 (
    echo ❌ 创建目录失败
    pause
    exit /b 1
)
echo ✅ 分发包目录创建成功

echo.
echo [2/5] 复制核心文件...
copy "start_client.py" "%PACKAGE_DIR%\"
copy "simple_desktop_client.py" "%PACKAGE_DIR%\"
copy "build_client.py" "%PACKAGE_DIR%\"
copy "finance_system.db" "%PACKAGE_DIR%\"
copy "install.bat" "%PACKAGE_DIR%\"
copy "README.md" "%PACKAGE_DIR%\"
copy "使用说明.txt" "%PACKAGE_DIR%\"
copy "客户端分发说明.md" "%PACKAGE_DIR%\"
copy "打包客户端.bat" "%PACKAGE_DIR%\"
echo ✅ 核心文件复制完成

echo.
echo [3/5] 复制模板文件...
xcopy "templates" "%PACKAGE_DIR%\templates\" /E /I /Y
if %errorlevel% neq 0 (
    echo ❌ 模板文件复制失败
    pause
    exit /b 1
)
echo ✅ 模板文件复制完成

echo.
echo [4/5] 构建可执行文件...
echo ⚠️ 正在构建可执行文件，这可能需要几分钟...
cd "%PACKAGE_DIR%"
python build_client.py
cd ..
if %errorlevel% neq 0 (
    echo ❌ 可执行文件构建失败
    echo 请手动运行: python build_client.py
) else (
    echo ✅ 可执行文件构建完成
)

echo.
echo [5/5] 创建压缩包...
echo ⚠️ 正在创建压缩包...
powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%' -DestinationPath '智能记账客户端_v1.0.0.zip' -Force"
if %errorlevel% neq 0 (
    echo ❌ 压缩包创建失败
    echo 请手动压缩 %PACKAGE_DIR% 文件夹
) else (
    echo ✅ 压缩包创建成功: 智能记账客户端_v1.0.0.zip
)

echo.
echo ========================================
echo 🎉 打包完成！
echo.
echo 📁 分发包目录: %PACKAGE_DIR%
echo 📦 压缩包文件: 智能记账客户端_v1.0.0.zip
echo.
echo 📋 包含文件:
echo   智能记账客户端.exe
echo   start_client.py
echo   simple_desktop_client.py
echo   build_client.py
echo   finance_system.db
echo   install.bat
echo   README.md
echo   使用说明.txt
echo   客户端分发说明.md
echo   templates/ (模板文件)
echo.
echo 🚀 使用方法:
echo   1. 解压压缩包
echo   2. 运行 install.bat 或 智能记账客户端.exe
echo ========================================
echo.

pause
