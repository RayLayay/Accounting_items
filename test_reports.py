"""
测试报告功能
验证报告生成和历史报告加载是否正常工作
"""

import requests
import json

# 测试配置
BASE_URL = "http://127.0.0.1:5000"
TEST_USER = "testuser"
TEST_PASSWORD = "test123"

def test_login():
    """测试登录"""
    print("🔐 测试登录...")
    session = requests.Session()
    
    login_data = {
        "username": TEST_USER,
        "password": TEST_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    if response.status_code == 200:
        print("✅ 登录成功")
        return session
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return None

def test_generate_monthly_report(session):
    """测试生成月度报告"""
    print("\n📊 测试生成月度报告...")
    
    report_data = {
        "year": 2025,
        "month": 11
    }
    
    response = session.post(
        f"{BASE_URL}/api/web/reports/monthly",
        json=report_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ 月度报告生成成功")
            print(f"   收入: ¥{result['report']['summary']['income']:.2f}")
            print(f"   支出: ¥{result['report']['summary']['expense']:.2f}")
            print(f"   余额: ¥{result['report']['summary']['balance']:.2f}")
            print(f"   记录数: {result['report']['summary']['records_count']}")
            return result['report']
        else:
            print(f"❌ 月度报告生成失败: {result.get('message')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    return None

def test_generate_yearly_report(session):
    """测试生成年度报告"""
    print("\n📊 测试生成年度报告...")
    
    report_data = {
        "year": 2025
    }
    
    response = session.post(
        f"{BASE_URL}/api/web/reports/yearly",
        json=report_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ 年度报告生成成功")
            print(f"   收入: ¥{result['report']['summary']['income']:.2f}")
            print(f"   支出: ¥{result['report']['summary']['expense']:.2f}")
            print(f"   余额: ¥{result['report']['summary']['balance']:.2f}")
            print(f"   记录数: {result['report']['summary']['records_count']}")
            return result['report']
        else:
            print(f"❌ 年度报告生成失败: {result.get('message')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    return None

def test_get_reports_list(session):
    """测试获取报告列表"""
    print("\n📋 测试获取报告列表...")
    
    response = session.get(f"{BASE_URL}/api/web/reports")
    
    if response.status_code == 200:
        reports = response.json()
        print(f"✅ 获取报告列表成功，共 {len(reports)} 个报告")
        
        for i, report in enumerate(reports, 1):
            print(f"   {i}. {report['title']} ({report['report_type']})")
            print(f"      生成时间: {report['generated_at']}")
        
        return reports
    else:
        print(f"❌ 获取报告列表失败: {response.status_code}")
    
    return []

def test_get_report_content(session, report_id):
    """测试获取报告内容"""
    print(f"\n📄 测试获取报告内容 (ID: {report_id})...")
    
    response = session.get(f"{BASE_URL}/api/web/reports/{report_id}")
    
    if response.status_code == 200:
        content = response.json()
        if content:
            print("✅ 获取报告内容成功")
            print(f"   收入: ¥{content['summary']['income']:.2f}")
            print(f"   支出: ¥{content['summary']['expense']:.2f}")
            print(f"   余额: ¥{content['summary']['balance']:.2f}")
            return content
        else:
            print("❌ 报告内容为空")
    else:
        print(f"❌ 获取报告内容失败: {response.status_code}")
    
    return None

def main():
    """主测试函数"""
    print("=" * 50)
    print("🧪 智能记账客户端 - 报告功能测试")
    print("=" * 50)
    
    # 测试登录
    session = test_login()
    if not session:
        print("❌ 测试终止：登录失败")
        return
    
    # 测试生成月度报告
    monthly_report = test_generate_monthly_report(session)
    
    # 测试生成年度报告
    yearly_report = test_generate_yearly_report(session)
    
    # 测试获取报告列表
    reports = test_get_reports_list(session)
    
    # 测试获取报告内容
    if reports:
        test_get_report_content(session, reports[0]['id'])
    
    print("\n" + "=" * 50)
    print("🎉 报告功能测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
