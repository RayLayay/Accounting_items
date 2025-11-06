"""
智能记账客户端 - 启动器
提供更友好的用户界面和错误处理
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_requirements():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查是否已打包
    if getattr(sys, 'frozen', False):
        print("✅ 运行在打包环境中")
        return True
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ Python版本过低，需要Python 3.7+")
        return False
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要模块
    required_modules = ['flask', 'sqlite3']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ 缺少必要模块: {', '.join(missing_modules)}")
        print("请运行: pip install flask")
        return False
    
    print("✅ 所有必要模块已安装")
    return True

def start_server():
    """启动服务器"""
    print("🚀 启动智能记账客户端...")
    
    try:
        # 如果是打包环境，直接运行主程序
        if getattr(sys, 'frozen', False):
            # 在打包环境中，simple_desktop_client.py已经被打包进exe
            import simple_desktop_client
            simple_desktop_client.main()
        else:
            # 在开发环境中，运行simple_desktop_client.py
            subprocess.run([sys.executable, 'simple_desktop_client.py'])
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n请尝试以下解决方案:")
        print("1. 检查端口5000是否被占用")
        print("2. 重新安装依赖: pip install flask")
        print("3. 重启电脑")
        return False
    
    return True

def open_browser():
    """打开浏览器"""
    print("🌐 正在打开浏览器...")
    time.sleep(3)  # 等待服务启动
    
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器: {e}")
        print("请手动访问: http://127.0.0.1:5000")

def show_welcome():
    """显示欢迎信息"""
    print("=" * 60)
    print("💰 智能记账客户端")
    print("=" * 60)
    print("功能特性:")
    print("  • 每日记账和快速操作")
    print("  • 月度/年度财务报告")
    print("  • 丰富的数据可视化图表")
    print("  • 多用户支持")
    print("  • 本地数据存储")
    print()
    print("默认账号: testuser / test123")
    print("=" * 60)
    print()

def main():
    """主函数"""
    show_welcome()
    
    # 检查环境
    if not check_requirements():
        print("\n❌ 环境检查失败，无法启动")
        input("按回车键退出...")
        return
    
    # 在后台线程中打开浏览器
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务器
    print("\n🎯 正在启动服务...")
    print("服务地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    print("-" * 40)
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        print("服务已停止")
    except Exception as e:
        print(f"\n❌ 服务异常停止: {e}")

if __name__ == '__main__':
    main()
