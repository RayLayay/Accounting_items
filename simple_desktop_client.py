"""
智能记账客户端 - 简化桌面版
将后端服务集成到主程序中，避免外部进程调用问题
"""

import sys
import os
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import json
import time

# 设置当前工作目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    base_path = sys._MEIPASS
else:
    # 如果是开发环境
    base_path = os.path.dirname(os.path.abspath(__file__))

# 设置模板目录
template_dir = os.path.join(base_path, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'desktop-finance-app-secret-2024'

# 数据库初始化
def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('finance_system.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 检查是否已有用户数据，如果没有才创建测试用户
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        # 创建默认测试用户
        password_hash = hashlib.sha256('test123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, password, email) 
            VALUES (?, ?, ?)
        ''', ('testuser', password_hash, 'test@example.com'))
    
    conn.commit()
    conn.close()

# 密码加密
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# API路由
@app.route('/')
def index():
    """主页面"""
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[1] == hash_password(password):
            session['user_id'] = user[0]
            session['username'] = username
            session['sync_token'] = secrets.token_hex(16)
            return redirect('/')
        else:
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email', '')
        
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空')
        
        try:
            conn = sqlite3.connect('finance_system.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, email) 
                VALUES (?, ?, ?)
            ''', (username, hash_password(password), email))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('register.html', error='用户名已存在')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect('/login')

@app.route('/api/records', methods=['GET'])
def get_records():
    """获取记录"""
    if 'user_id' not in session:
        return jsonify([])
    
    conn = sqlite3.connect('finance_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, amount, category, type, description, date 
        FROM records WHERE user_id = ? ORDER BY date DESC
    ''', (session['user_id'],))
    
    records = []
    for row in cursor.fetchall():
        records.append({
            'id': row[0],
            'amount': row[1],
            'category': row[2],
            'type': row[3],
            'description': row[4],
            'date': row[5]
        })
    
    conn.close()
    return jsonify(records)

@app.route('/api/records', methods=['POST'])
def add_record():
    """添加记录"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    data = request.get_json()
    amount = data.get('amount')
    category = data.get('category')
    record_type = data.get('type')
    description = data.get('description', '')
    record_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO records (user_id, amount, category, type, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], amount, category, record_type, description, record_date))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除记录"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM records WHERE id = ? AND user_id = ?', 
                      (record_id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/summary')
def get_summary():
    """获取汇总数据"""
    if 'user_id' not in session:
        return jsonify({'income': 0, 'expense': 0, 'balance': 0})
    
    conn = sqlite3.connect('finance_system.db')
    cursor = conn.cursor()
    
    # 总收入
    cursor.execute('SELECT SUM(amount) FROM records WHERE user_id = ? AND type = "income"', 
                  (session['user_id'],))
    income = cursor.fetchone()[0] or 0
    
    # 总支出
    cursor.execute('SELECT SUM(amount) FROM records WHERE user_id = ? AND type = "expense"', 
                  (session['user_id'],))
    expense = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'income': income,
        'expense': expense,
        'balance': income - expense
    })

@app.route('/api/monthly-data')
def get_monthly_data():
    """获取月度数据"""
    if 'user_id' not in session:
        return jsonify([])
    
    conn = sqlite3.connect('finance_system.db')
    cursor = conn.cursor()
    
    # 获取最近6个月的数据
    months = []
    for i in range(5, -1, -1):
        month = (datetime.now() - timedelta(days=30*i)).strftime('%Y-%m')
        months.append(month)
    
    monthly_data = []
    for month in months:
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END)
            FROM records 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        ''', (session['user_id'], month))
        
        result = cursor.fetchone()
        income = result[0] or 0
        expense = result[1] or 0
        
        monthly_data.append({
            'month': month,
            'income': income,
            'expense': expense,
            'balance': income - expense
        })
    
    conn.close()
    return jsonify(monthly_data)

@app.route('/api/categories')
def get_categories():
    """获取分类"""
    return jsonify({
        'income': ['工资', '奖金', '投资', '其他收入'],
        'expense': ['餐饮', '交通', '购物', '娱乐', '医疗', '教育', '住房', '其他支出']
    })

@app.route('/reports')
def reports():
    """报告页面"""
    if 'user_id' not in session:
        return redirect('/login')
    
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    current_year = now.year
    
    return render_template('reports.html', 
                         current_month=current_month, 
                         current_year=current_year)

def open_browser():
    """打开浏览器"""
    time.sleep(3)  # 等待服务启动
    webbrowser.open('http://127.0.0.1:5000')

def main():
    """主函数"""
    print("=" * 50)
    print("💰 智能记账客户端 - 简化桌面版")
    print("=" * 50)
    
    # 初始化数据库
    init_database()
    print("✅ 数据库初始化完成")
    
    # 在后台线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\n🎉 客户端启动成功！")
    print("访问地址: http://127.0.0.1:5000")
    print("测试账号: testuser / test123")
    print("\n按 Ctrl+C 停止服务")
    
    # 启动Flask应用
    try:
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n正在停止服务...")
        print("服务已停止")

if __name__ == '__main__':
    main()
