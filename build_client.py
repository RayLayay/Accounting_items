"""
智能记账客户端 - 打包脚本
使用PyInstaller将项目打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """检查必要的依赖"""
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
        return True
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False

def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_client.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates/*.html', 'templates'),
        ('backend_api.py', '.'),
        ('README.md', '.'),
        ('记账客户端使用说明.md', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'requests',
        'sqlite3',
        'hashlib',
        'secrets',
        'calendar',
        'threading',
        'datetime',
        'json',
        'webbrowser',
        'subprocess',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='智能记账客户端',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，便于调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)
'''
    
    with open('智能记账客户端.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ 创建 spec 文件成功")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 使用PyInstaller构建
        result = subprocess.run([
            'pyinstaller',
            '智能记账客户端.spec',
            '--clean',
            '--noconfirm'
        ], capture_output=True, text=True, encoding='gbk')
        
        if result.returncode == 0:
            print("✅ 构建成功！")
            print(f"可执行文件位置: dist/智能记账客户端.exe")
            return True
        else:
            print("❌ 构建失败")
            print("错误信息:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        return False

def create_installer_script():
    """创建安装脚本"""
    installer_content = '''@echo off
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
'''
    
    with open('install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    print("✅ 创建安装脚本成功")

def create_readme():
    """创建使用说明"""
    readme_content = '''# 智能记账客户端 - 桌面版

## 🎯 简介

这是一个功能完整的智能记账客户端，支持多用户登录、数据同步、自动报告生成和丰富的数据可视化功能。

## ✅ 功能特性

- ✅ **每日记账功能** - 完整的记账表单和快速操作
- ✅ **月底自动报告** - 自动生成详细的月度财务报告  
- ✅ **年底自动报告** - 自动生成全面的年度财务报告
- ✅ **时间段数据可视化** - 支持任意时间段的数据分析和图表展示
- ✅ **多用户支持** - 完整的用户注册登录系统
- ✅ **数据同步** - 实时数据同步

## 🚀 快速开始

### 方法一：直接运行（推荐）
1. 双击运行 `智能记账客户端.exe`
2. 系统会自动打开浏览器访问应用
3. 使用测试账号: `testuser` / `test123`

### 方法二：源码运行
1. 确保安装 Python 3.7+
2. 安装依赖: `pip install flask requests`
3. 运行: `python desktop_client.py`

## 📊 系统界面

- **仪表板**: 快速记账、数据统计、图表展示
- **报告分析**: 生成月度/年度报告，时间范围分析
- **用户管理**: 注册、登录、退出

## 🔧 技术架构

- **后端**: Flask + SQLite
- **前端**: 原生JavaScript + ECharts图表
- **数据库**: SQLite（无需额外配置）

## 📁 文件说明

- `智能记账客户端.exe` - 主程序
- `backend_api.py` - 后端API服务
- `desktop_client.py` - 桌面客户端
- `templates/` - HTML模板文件
- `finance_system.db` - 数据库文件（自动生成）

## 🆘 常见问题

### Q: 启动时提示端口被占用？
A: 请关闭其他占用5000或5001端口的程序，或重启电脑。

### Q: 浏览器没有自动打开？
A: 手动访问: http://127.0.0.1:5000

### Q: 忘记密码？
A: 目前不支持密码找回，请重新注册账号。

## 📞 技术支持

如有问题，请检查：
1. 是否安装了必要的依赖
2. 防火墙是否阻止了本地服务
3. 浏览器是否支持现代JavaScript特性

---
祝您使用愉快！💰
'''
    
    with open('使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ 创建使用说明成功")

def main():
    """主函数"""
    print("=" * 50)
    print("💰 智能记账客户端 - 打包工具")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 创建必要的文件
    create_spec_file()
    create_installer_script()
    create_readme()
    
    # 构建可执行文件
    if build_executable():
        print("\n🎉 打包完成！")
        print("生成的文件:")
        print("  - dist/智能记账客户端.exe (主程序)")
        print("  - install.bat (安装脚本)") 
        print("  - 使用说明.txt (使用说明)")
        print("\n📦 分发说明:")
        print("1. 将整个 dist 文件夹分发给用户")
        print("2. 用户双击 智能记账客户端.exe 即可运行")
        print("3. 或运行 install.bat 进行安装")
    else:
        print("\n❌ 打包失败，请检查错误信息")

if __name__ == '__main__':
    main()
