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
import calendar

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
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

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
    """获取记录 - 修复数据加载异常，合并两个表的数据"""
    if 'user_id' not in session:
        return jsonify([])
    
    try:
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 合并查询两个表的数据，避免数据分散问题
        records = []
        
        # 查询records表
        cursor.execute('''
            SELECT id, amount, category, type, description, date 
            FROM records WHERE user_id = ? ORDER BY date DESC
        ''', (session['user_id'],))
        
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'amount': row[1],
                'category': row[2],
                'type': row[3],
                'description': row[4],
                'date': row[5],
                'source': 'records'
            })
        
        # 查询finance_records表并转换为相同格式
        cursor.execute('''
            SELECT id, amount, category, record_type, description, record_date, created_at
            FROM finance_records WHERE user_id = ? ORDER BY record_date DESC
        ''', (session['user_id'],))
        
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'amount': row[1],
                'category': row[2],
                'type': row[3],  # record_type -> type
                'description': row[4],
                'date': row[5],  # record_date -> date
                'created_at': row[6],
                'source': 'finance_records'
            })
        
        # 按日期排序
        records.sort(key=lambda x: x['date'], reverse=True)
        
        conn.close()
        return jsonify(records)
    except Exception as e:
        print(f"获取记录失败: {e}")
        return jsonify([])

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
    """获取汇总数据 - 修复数据加载异常，合并两个表的数据"""
    if 'user_id' not in session:
        return jsonify({'income': 0, 'expense': 0, 'balance': 0})
    
    conn = sqlite3.connect('finance_system.db')
    cursor = conn.cursor()
    
    # 总收入 - 合并两个表
    cursor.execute('SELECT SUM(amount) FROM records WHERE user_id = ? AND type = "income"', 
                  (session['user_id'],))
    income_records = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(amount) FROM finance_records WHERE user_id = ? AND record_type = "income"', 
                  (session['user_id'],))
    income_finance_records = cursor.fetchone()[0] or 0
    
    # 总支出 - 合并两个表
    cursor.execute('SELECT SUM(amount) FROM records WHERE user_id = ? AND type = "expense"', 
                  (session['user_id'],))
    expense_records = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(amount) FROM finance_records WHERE user_id = ? AND record_type = "expense"', 
                  (session['user_id'],))
    expense_finance_records = cursor.fetchone()[0] or 0
    
    total_income = income_records + income_finance_records
    total_expense = expense_records + expense_finance_records
    
    conn.close()
    
    return jsonify({
        'income': total_income,
        'expense': total_expense,
        'balance': total_income - total_expense
    })

@app.route('/api/monthly-data')
def get_monthly_data():
    """获取月度数据 - 修复数据加载异常，合并两个表的数据"""
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
        # 查询records表
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END)
            FROM records 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        ''', (session['user_id'], month))
        
        result_records = cursor.fetchone()
        income_records = result_records[0] or 0
        expense_records = result_records[1] or 0
        
        # 查询finance_records表
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN record_type = 'income' THEN amount ELSE 0 END),
                SUM(CASE WHEN record_type = 'expense' THEN amount ELSE 0 END)
            FROM finance_records 
            WHERE user_id = ? AND strftime('%Y-%m', record_date) = ?
        ''', (session['user_id'], month))
        
        result_finance_records = cursor.fetchone()
        income_finance_records = result_finance_records[0] or 0
        expense_finance_records = result_finance_records[1] or 0
        
        # 合并两个表的数据
        total_income = income_records + income_finance_records
        total_expense = expense_records + expense_finance_records
        
        monthly_data.append({
            'month': month,
            'income': total_income,
            'expense': total_expense,
            'balance': total_income - total_expense
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

# 报告相关API
@app.route('/api/web/reports', methods=['GET'])
def get_reports_list():
    """获取报告列表"""
    if 'user_id' not in session:
        return jsonify([])
    
    try:
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 检查reports表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
        if not cursor.fetchone():
            return jsonify([])
        
        cursor.execute('''
            SELECT id, report_type, period, title, generated_at 
            FROM reports WHERE user_id = ? ORDER BY generated_at DESC
        ''', (session['user_id'],))
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': row[0],
                'report_type': row[1],
                'period': row[2],
                'title': row[3],
                'generated_at': row[4]
            })
        
        conn.close()
        return jsonify(reports)
    except Exception as e:
        print(f"获取报告列表失败: {e}")
        return jsonify([])

@app.route('/api/web/reports/<int:report_id>', methods=['GET'])
def get_report_content(report_id):
    """获取报告内容"""
    if 'user_id' not in session:
        return jsonify({})
    
    try:
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM reports WHERE id = ? AND user_id = ?
        ''', (report_id, session['user_id']))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        else:
            return jsonify({})
    except Exception as e:
        print(f"获取报告内容失败: {e}")
        return jsonify({})

@app.route('/api/web/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """删除报告"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 检查报告是否存在且属于当前用户
        cursor.execute('''
            SELECT id FROM reports WHERE id = ? AND user_id = ?
        ''', (report_id, session['user_id']))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '报告不存在或无权删除'})
        
        # 删除报告
        cursor.execute('DELETE FROM reports WHERE id = ? AND user_id = ?', 
                      (report_id, session['user_id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '报告删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除报告失败: {str(e)}'})

@app.route('/api/web/reports/monthly', methods=['POST'])
def generate_monthly_report():
    """生成月度报告"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        data = request.get_json()
        year = data.get('year', datetime.now().year)
        month = data.get('month', datetime.now().month)
        
        # 获取月度数据
        start_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day}"
        
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 获取记录
        records = []
        
        # 查询records表
        cursor.execute('''
            SELECT amount, category, type, description, date 
            FROM records WHERE user_id = ? AND date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 查询finance_records表
        cursor.execute('''
            SELECT amount, category, record_type, description, record_date 
            FROM finance_records WHERE user_id = ? AND record_date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 计算汇总
        income = sum(r['amount'] for r in records if r['type'] == 'income')
        expense = sum(r['amount'] for r in records if r['type'] == 'expense')
        balance = income - expense
        
        # 分类统计
        category_stats = {}
        for record in records:
            category = record['category']
            if category not in category_stats:
                category_stats[category] = {'income': 0, 'expense': 0}
            
            if record['type'] == 'income':
                category_stats[category]['income'] += record['amount']
            else:
                category_stats[category]['expense'] += record['amount']
        
        # 大额记录
        top_expenses = sorted(
            [r for r in records if r['type'] == 'expense'],
            key=lambda x: x['amount'],
            reverse=True
        )[:5]
        
        top_incomes = sorted(
            [r for r in records if r['type'] == 'income'],
            key=lambda x: x['amount'],
            reverse=True
        )[:5]
        
        # 生成报告内容
        report_content = {
            'summary': {
                'income': income,
                'expense': expense,
                'balance': balance,
                'records_count': len(records)
            },
            'category_stats': category_stats,
            'top_expenses': top_expenses,
            'top_incomes': top_incomes
        }
        
        # 保存报告
        report_title = f"{year}年{month}月财务报告"
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 确保reports表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                period TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO reports (user_id, report_type, period, title, content, generated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], 'monthly', f"{year}-{month:02d}", report_title, json.dumps(report_content, ensure_ascii=False), generated_at))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '月度报告生成成功',
            'report': report_content
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成月度报告失败: {str(e)}'})

@app.route('/api/web/reports/yearly', methods=['POST'])
def generate_yearly_report():
    """生成年度报告"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        data = request.get_json()
        year = data.get('year', datetime.now().year)
        
        # 获取年度数据
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 获取记录
        records = []
        
        # 查询records表
        cursor.execute('''
            SELECT amount, category, type, description, date 
            FROM records WHERE user_id = ? AND date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 查询finance_records表
        cursor.execute('''
            SELECT amount, category, record_type, description, record_date 
            FROM finance_records WHERE user_id = ? AND record_date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 计算汇总
        income = sum(r['amount'] for r in records if r['type'] == 'income')
        expense = sum(r['amount'] for r in records if r['type'] == 'expense')
        balance = income - expense
        
        # 分类统计
        category_stats = {}
        for record in records:
            category = record['category']
            if category not in category_stats:
                category_stats[category] = {'income': 0, 'expense': 0}
            
            if record['type'] == 'income':
                category_stats[category]['income'] += record['amount']
            else:
                category_stats[category]['expense'] += record['amount']
        
        # 月度趋势
        monthly_trend = []
        for month in range(1, 13):
            month_start = f"{year}-{month:02d}-01"
            month_end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
            
            month_income = sum(r['amount'] for r in records if r['type'] == 'income' and month_start <= r['date'] <= month_end)
            month_expense = sum(r['amount'] for r in records if r['type'] == 'expense' and month_start <= r['date'] <= month_end)
            
            monthly_trend.append({
                'month': f"{year}-{month:02d}",
                'income': month_income,
                'expense': month_expense,
                'balance': month_income - month_expense
            })
        
        # 大额记录
        top_expenses = sorted(
            [r for r in records if r['type'] == 'expense'],
            key=lambda x: x['amount'],
            reverse=True
        )[:10]
        
        top_incomes = sorted(
            [r for r in records if r['type'] == 'income'],
            key=lambda x: x['amount'],
            reverse=True
        )[:10]
        
        # 生成报告内容
        report_content = {
            'summary': {
                'income': income,
                'expense': expense,
                'balance': balance,
                'records_count': len(records)
            },
            'category_stats': category_stats,
            'monthly_trend': monthly_trend,
            'top_expenses': top_expenses,
            'top_incomes': top_incomes
        }
        
        # 保存报告
        report_title = f"{year}年度财务报告"
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 确保reports表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                period TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO reports (user_id, report_type, period, title, content, generated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], 'yearly', f"{year}", report_title, json.dumps(report_content, ensure_ascii=False), generated_at))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '年度报告生成成功',
            'report': report_content
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成年度报告失败: {str(e)}'})

# 数据分析API
@app.route('/api/web/analysis/time-range')
def time_range_analysis():
    """时间范围分析"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'message': '请提供开始日期和结束日期'})
        
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 获取记录
        records = []
        
        # 查询records表
        cursor.execute('''
            SELECT amount, category, type, description, date 
            FROM records WHERE user_id = ? AND date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 查询finance_records表
        cursor.execute('''
            SELECT amount, category, record_type, description, record_date 
            FROM finance_records WHERE user_id = ? AND record_date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 按日期分组
        daily_data = {}
        for record in records:
            date_key = record['date'][:10]
            if date_key not in daily_data:
                daily_data[date_key] = {'income': 0, 'expense': 0}
            
            if record['type'] == 'income':
                daily_data[date_key]['income'] += record['amount']
            else:
                daily_data[date_key]['expense'] += record['amount']
        
        # 按分类统计
        category_data = {}
        for record in records:
            category = record['category']
            if category not in category_data:
                category_data[category] = {'income': 0, 'expense': 0}
            
            if record['type'] == 'income':
                category_data[category]['income'] += record['amount']
            else:
                category_data[category]['expense'] += record['amount']
        
        # 计算统计指标
        total_income = sum(r['amount'] for r in records if r['type'] == 'income')
        total_expense = sum(r['amount'] for r in records if r['type'] == 'expense')
        avg_daily_income = total_income / len(daily_data) if daily_data else 0
        avg_daily_expense = total_expense / len(daily_data) if daily_data else 0
        
        # 大额记录
        top_incomes = sorted(
            [r for r in records if r['type'] == 'income'],
            key=lambda x: x['amount'],
            reverse=True
        )[:10]
        
        top_expenses = sorted(
            [r for r in records if r['type'] == 'expense'],
            key=lambda x: x['amount'],
            reverse=True
        )[:10]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'time_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_income': total_income,
                'total_expense': total_expense,
                'balance': total_income - total_expense,
                'records_count': len(records),
                'days_count': len(daily_data),
                'avg_daily_income': avg_daily_income,
                'avg_daily_expense': avg_daily_expense
            },
            'daily_data': daily_data,
            'category_data': category_data,
            'top_records': {
                'incomes': top_incomes,
                'expenses': top_expenses
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'时间范围分析失败: {str(e)}'})

@app.route('/api/web/analysis/category')
def category_analysis():
    """分类分析"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'message': '请提供开始日期和结束日期'})
        
        conn = sqlite3.connect('finance_system.db')
        cursor = conn.cursor()
        
        # 获取记录
        records = []
        
        # 查询records表
        cursor.execute('''
            SELECT amount, category, type, description, date 
            FROM records WHERE user_id = ? AND date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 查询finance_records表
        cursor.execute('''
            SELECT amount, category, record_type, description, record_date 
            FROM finance_records WHERE user_id = ? AND record_date BETWEEN ? AND ?
        ''', (session['user_id'], start_date, end_date))
        
        for row in cursor.fetchall():
            records.append({
                'amount': row[0],
                'category': row[1],
                'type': row[2],
                'description': row[3],
                'date': row[4]
            })
        
        # 分类统计
        category_stats = {}
        for record in records:
            category = record['category']
            if category not in category_stats:
                category_stats[category] = {
                    'income': 0,
                    'expense': 0,
                    'count': 0
                }
            
            category_stats[category]['count'] += 1
            
            if record['type'] == 'income':
                category_stats[category]['income'] += record['amount']
            else:
                category_stats[category]['expense'] += record['amount']
        
        # 计算占比
        total_income = sum(stats['income'] for stats in category_stats.values())
        total_expense = sum(stats['expense'] for stats in category_stats.values())
        
        for category, stats in category_stats.items():
            if total_income > 0:
                stats['income_percentage'] = (stats['income'] / total_income) * 100
            else:
                stats['income_percentage'] = 0
            
            if total_expense > 0:
                stats['expense_percentage'] = (stats['expense'] / total_expense) * 100
            else:
                stats['expense_percentage'] = 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'time_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_income': total_income,
                'total_expense': total_expense,
                'balance': total_income - total_expense,
                'records_count': len(records)
            },
            'category_stats': category_stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'分类分析失败: {str(e)}'})

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
