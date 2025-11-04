"""
双端记账系统 - 系统启动脚本
启动后端API服务和Web应用
"""

import subprocess
import sys
import time
import os
import threading

def start_backend():
    """启动后端API服务"""
    print("正在启动后端API服务...")
    try:
        # 启动后端服务
        backend_process = subprocess.Popen([
            sys.executable, 'backend_api.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待后端服务启动
        time.sleep(3)
        
        # 检查后端服务是否正常启动
        import requests
        try:
            response = requests.get('http://127.0.0.1:5001/api/auth/status', timeout=5)
            if response.status_code == 200:
                print("✅ 后端API服务启动成功 (端口: 5001)")
            else:
                print("❌ 后端API服务启动异常")
        except:
            print("❌ 后端API服务启动失败")
        
        return backend_process
    except Exception as e:
        print(f"启动后端服务失败: {e}")
        return None

def start_web():
    """启动Web应用"""
    print("正在启动Web应用...")
    try:
        # 启动Web应用
        web_process = subprocess.Popen([
            sys.executable, 'web_app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待Web应用启动
        time.sleep(3)
        
        # 检查Web应用是否正常启动
        import requests
        try:
            response = requests.get('http://127.0.0.1:5000/', timeout=5)
            if response.status_code == 200:
                print("✅ Web应用启动成功 (端口: 5000)")
            else:
                print("❌ Web应用启动异常")
        except:
            print("❌ Web应用启动失败")
        
        return web_process
    except Exception as e:
        print(f"启动Web应用失败: {e}")
        return None

def check_services():
    """检查服务状态"""
    print("\n🔍 检查服务状态...")
    
    import requests
    
    # 检查后端服务
    try:
        response = requests.get('http://127.0.0.1:5001/api/auth/status', timeout=5)
        if response.status_code == 200:
            print("✅ 后端API服务运行正常")
        else:
            print("❌ 后端API服务异常")
    except:
        print("❌ 后端API服务无法访问")
    
    # 检查Web应用
    try:
        response = requests.get('http://127.0.0.1:5000/', timeout=5)
        if response.status_code == 200:
            print("✅ Web应用运行正常")
        else:
            print("❌ Web应用异常")
    except:
        print("❌ Web应用无法访问")

def create_test_data():
    """创建测试数据"""
    print("\n📊 创建测试数据...")
    
    import requests
    import json
    from datetime import datetime, timedelta
    
    # 注册测试用户
    try:
        response = requests.post('http://127.0.0.1:5001/api/auth/register', json={
            'username': 'testuser',
            'password': 'test123',
            'email': 'test@example.com'
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 测试用户创建成功")
                sync_token = result.get('sync_token')
                
                # 添加测试记录
                headers = {'X-Sync-Token': sync_token}
                
                # 添加一些收入记录
                income_categories = ['工资', '奖金', '投资']
                for i in range(5):
                    date = (datetime.now() - timedelta(days=i*7)).strftime('%Y-%m-%d')
                    response = requests.post('http://127.0.0.1:5001/api/records', json={
                        'amount': 5000 + i * 1000,
                        'category': income_categories[i % len(income_categories)],
                        'type': 'income',
                        'description': f'测试收入记录 {i+1}',
                        'date': date
                    }, headers=headers)
                
                # 添加一些支出记录
                expense_categories = ['餐饮', '购物', '交通', '娱乐', '医疗']
                for i in range(10):
                    date = (datetime.now() - timedelta(days=i*3)).strftime('%Y-%m-%d')
                    response = requests.post('http://127.0.0.1:5001/api/records', json={
                        'amount': 100 + i * 50,
                        'category': expense_categories[i % len(expense_categories)],
                        'type': 'expense',
                        'description': f'测试支出记录 {i+1}',
                        'date': date
                    }, headers=headers)
                
                print("✅ 测试数据创建完成")
            else:
                print("⚠️ 测试用户已存在，跳过创建")
        else:
            print("❌ 创建测试用户失败")
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("💰 双端记账系统启动器")
    print("=" * 50)
    
    # 检查Python环境
    print(f"Python版本: {sys.version}")
    
    # 检查依赖
    print("\n📦 检查依赖...")
    try:
        import flask
        import requests
        import sqlite3
        print("✅ 所有依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install flask requests")
        return
    
    # 启动服务
    backend_process = start_backend()
    if not backend_process:
        return
    
    web_process = start_web()
    if not web_process:
        return
    
    # 等待服务完全启动
    time.sleep(2)
    
    # 检查服务状态
    check_services()
    
    # 创建测试数据
    create_test_data()
    
    print("\n" + "=" * 50)
    print("🎉 系统启动完成！")
    print("=" * 50)
    print("\n访问地址:")
    print("📱 Web端: http://127.0.0.1:5000")
    print("🔧 后端API: http://127.0.0.1:5001")
    print("\n测试账号:")
    print("👤 用户名: testuser")
    print("🔑 密码: test123")
    print("\n功能说明:")
    print("✅ 多用户登录系统")
    print("✅ 财务记录管理")
    print("✅ 数据统计分析")
    print("✅ 自动报告生成")
    print("✅ 移动端数据同步")
    print("✅ 可视化图表展示")
    print("\n按 Ctrl+C 停止所有服务")
    
    try:
        # 保持服务运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n正在停止服务...")
        if backend_process:
            backend_process.terminate()
        if web_process:
            web_process.terminate()
        print("服务已停止")

if __name__ == '__main__':
    main()
