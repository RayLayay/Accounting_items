"""
双端记账系统 - Web端应用
支持多用户登录和数据同步
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'web-finance-app-secret-2024'

# 后端API配置
API_BASE_URL = "http://127.0.0.1:5001"

class APIClient:
    """API客户端"""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def register(self, username, password, email=""):
        """用户注册"""
        url = f"{self.base_url}/api/auth/register"
        data = {
            'username': username,
            'password': password,
            'email': email
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def login(self, username, password):
        """用户登录"""
        url = f"{self.base_url}/api/auth/login"
        data = {
            'username': username,
            'password': password
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def logout(self):
        """用户登出"""
        url = f"{self.base_url}/api/auth/logout"
        response = self.session.post(url)
        return response.json()
    
    def get_auth_status(self):
        """获取认证状态"""
        url = f"{self.base_url}/api/auth/status"
        response = self.session.get(url)
        return response.json()
    
    def get_records(self):
        """获取记录"""
        url = f"{self.base_url}/api/records"
        response = self.session.get(url)
        return response.json()
    
    def add_record(self, record_data):
        """添加记录"""
        url = f"{self.base_url}/api/records"
        response = self.session.post(url, json=record_data)
        return response.json()
    
    def delete_record(self, record_id):
        """删除记录"""
        url = f"{self.base_url}/api/records/{record_id}"
        response = self.session.delete(url)
        return response.json()
    
    def get_summary(self):
        """获取汇总数据"""
        url = f"{self.base_url}/api/summary"
        response = self.session.get(url)
        return response.json()
    
    def get_monthly_data(self):
        """获取月度数据"""
        url = f"{self.base_url}/api/monthly-data"
        response = self.session.get(url)
        return response.json()
    
    def get_categories(self):
        """获取分类"""
        url = f"{self.base_url}/api/categories"
        response = self.session.get(url)
        return response.json()

# 全局API客户端
api_client = APIClient()

@app.route('/')
def index():
    """主页面"""
    auth_status = api_client.get_auth_status()
    if not auth_status.get('logged_in'):
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        result = api_client.login(username, password)
        if result.get('success'):
            session['username'] = username
            session['sync_token'] = result.get('sync_token')
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error=result.get('message'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email', '')
        
        result = api_client.register(username, password, email)
        if result.get('success'):
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=result.get('message'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """登出"""
    api_client.logout()
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/web/records', methods=['GET'])
def web_get_records():
    """获取记录（Web API）"""
    try:
        result = api_client.get_records()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/records', methods=['POST'])
def web_add_record():
    """添加记录（Web API）"""
    try:
        data = request.get_json()
        result = api_client.add_record(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/records/<int:record_id>', methods=['DELETE'])
def web_delete_record(record_id):
    """删除记录（Web API）"""
    try:
        result = api_client.delete_record(record_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/summary')
def web_get_summary():
    """获取汇总数据（Web API）"""
    try:
        result = api_client.get_summary()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/monthly-data')
def web_get_monthly_data():
    """获取月度数据（Web API）"""
    try:
        result = api_client.get_monthly_data()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/categories')
def web_get_categories():
    """获取分类（Web API）"""
    try:
        result = api_client.get_categories()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/reports')
def reports():
    """报告分析页面"""
    if 'username' not in session:
        return redirect('/login')
    
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    current_year = now.year
    
    return render_template('reports.html', 
                         current_month=current_month, 
                         current_year=current_year)

@app.route('/api/web/reports/monthly', methods=['POST'])
def web_generate_monthly_report():
    """生成月度报告（Web API）"""
    try:
        data = request.get_json()
        url = f"{API_BASE_URL}/api/reports/monthly"
        response = requests.post(url, json=data, cookies=request.cookies)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/reports/yearly', methods=['POST'])
def web_generate_yearly_report():
    """生成年度报告（Web API）"""
    try:
        data = request.get_json()
        url = f"{API_BASE_URL}/api/reports/yearly"
        response = requests.post(url, json=data, cookies=request.cookies)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/reports')
def web_get_reports():
    """获取报告列表（Web API）"""
    try:
        report_type = request.args.get('type')
        url = f"{API_BASE_URL}/api/reports"
        if report_type:
            url += f"?type={report_type}"
        response = requests.get(url, cookies=request.cookies)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/reports/<int:report_id>')
def web_get_report_content(report_id):
    """获取报告内容（Web API）"""
    try:
        url = f"{API_BASE_URL}/api/reports/{report_id}"
        response = requests.get(url, cookies=request.cookies)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/analysis/time-range')
def web_get_time_analysis():
    """获取时间范围分析（Web API）"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        url = f"{API_BASE_URL}/api/analysis/time-range?start_date={start_date}&end_date={end_date}"
        response = requests.get(url, cookies=request.cookies)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/web/analysis/category')
def web_get_category_analysis():
    """获取分类分析（Web API）"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        url = f"{API_BASE_URL}/api/analysis/category?start_date={start_date}&end_date={end_date}"
        response = requests.get(url, cookies=request.cookies)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    print("双端记账系统Web应用启动中...")
    print("访问地址: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
