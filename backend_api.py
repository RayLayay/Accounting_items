"""
双端记账系统 - 后端API服务
支持Web端和移动端数据互通，多用户登录
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import json
import os
import datetime
from datetime import datetime as dt
import calendar
import hashlib
import secrets
from typing import List, Dict, Any
import sqlite3
import threading

app = Flask(__name__)
app.secret_key = 'finance-app-secret-key-2024'
CORS(app, supports_credentials=True)

# 数据库配置
DB_FILE = "finance_system.db"

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                sync_token TEXT
            )
        ''')
        
        # 财务记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                record_type TEXT NOT NULL,
                description TEXT,
                record_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sync_id TEXT UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 同步记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                last_sync_time TEXT NOT NULL,
                sync_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 报告表
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
        
        # 分析数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                data_type TEXT NOT NULL,
                period TEXT NOT NULL,
                data_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_file)

class UserManager:
    """用户管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str = "") -> Dict[str, Any]:
        """注册用户"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            created_at = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            sync_token = secrets.token_hex(16)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, created_at, sync_token)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, email, created_at, sync_token))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                'success': True,
                'user_id': user_id,
                'sync_token': sync_token,
                'message': '注册成功'
            }
        except sqlite3.IntegrityError:
            return {'success': False, 'message': '用户名已存在'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """用户认证"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, password_hash, sync_token FROM users WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            if not result:
                return {'success': False, 'message': '用户不存在'}
            
            user_id, stored_hash, sync_token = result
            password_hash = self.hash_password(password)
            
            if stored_hash == password_hash:
                # 更新最后登录时间
                last_login = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE users SET last_login = ? WHERE id = ?
                ''', (last_login, user_id))
                conn.commit()
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'sync_token': sync_token,
                    'message': '登录成功'
                }
            else:
                return {'success': False, 'message': '密码错误'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()
    
    def get_user_by_token(self, sync_token: str) -> Dict[str, Any]:
        """通过同步令牌获取用户信息"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username FROM users WHERE sync_token = ?
            ''', (sync_token,))
            
            result = cursor.fetchone()
            if result:
                return {'success': True, 'user_id': result[0], 'username': result[1]}
            else:
                return {'success': False, 'message': '无效的同步令牌'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()

class FinanceManager:
    """财务管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.categories = {
            'income': ['工资', '奖金', '投资', '兼职', '其他收入'],
            'expense': ['餐饮', '购物', '交通', '娱乐', '医疗', '教育', '住房', '其他支出']
        }
    
    def add_record(self, user_id: int, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加财务记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            sync_id = secrets.token_hex(16)
            created_at = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_at = created_at
            
            cursor.execute('''
                INSERT INTO finance_records 
                (user_id, amount, category, record_type, description, record_date, created_at, updated_at, sync_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                record_data['amount'],
                record_data['category'],
                record_data['type'],
                record_data.get('description', ''),
                record_data.get('date', created_at),
                created_at,
                updated_at,
                sync_id
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            
            return {
                'success': True,
                'record_id': record_id,
                'sync_id': sync_id,
                'message': '记录添加成功'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()
    
    def get_user_records(self, user_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取用户记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, amount, category, record_type, description, record_date, created_at, sync_id
                FROM finance_records 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if start_date and end_date:
                query += ' AND record_date BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            elif start_date:
                query += ' AND record_date >= ?'
                params.append(start_date)
            elif end_date:
                query += ' AND record_date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY record_date DESC, created_at DESC'
            
            cursor.execute(query, params)
            records = []
            
            for row in cursor.fetchall():
                records.append({
                    'id': row[0],
                    'amount': row[1],
                    'category': row[2],
                    'type': row[3],
                    'description': row[4] or '',
                    'date': row[5],
                    'created_at': row[6],
                    'sync_id': row[7]
                })
            
            return records
        except Exception as e:
            print(f"获取记录失败: {e}")
            return []
        finally:
            conn.close()
    
    def delete_record(self, user_id: int, record_id: int) -> Dict[str, Any]:
        """删除记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM finance_records WHERE id = ? AND user_id = ?
            ''', (record_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return {'success': True, 'message': '记录删除成功'}
            else:
                return {'success': False, 'message': '记录不存在或无权限'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()
    
    def get_summary(self, user_id: int, year: int = None, month: int = None) -> Dict[str, Any]:
        """获取汇总数据"""
        if year is None:
            year = dt.now().year
        if month is None:
            month = dt.now().month
        
        start_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day}"
        
        records = self.get_user_records(user_id, start_date, end_date)
        
        income = sum(r['amount'] for r in records if r['type'] == 'income')
        expense = sum(r['amount'] for r in records if r['type'] == 'expense')
        balance = income - expense
        
        return {
            'income': income,
            'expense': expense,
            'balance': balance,
            'records_count': len(records)
        }
    
    def get_monthly_data(self, user_id: int, year: int = None) -> List[Dict[str, Any]]:
        """获取月度数据"""
        if year is None:
            year = dt.now().year
        
        monthly_data = []
        for month in range(1, 13):
            monthly_summary = self.get_summary(user_id, year, month)
            monthly_data.append({
                'month': f"{year}-{month:02d}",
                'income': monthly_summary['income'],
                'expense': monthly_summary['expense'],
                'balance': monthly_summary['balance']
            })
        
        return monthly_data

class ReportManager:
    """报告管理器"""
    
    def __init__(self, db_manager, finance_manager):
        self.db_manager = db_manager
        self.finance_manager = finance_manager
    
    def generate_monthly_report(self, user_id: int, year: int, month: int) -> Dict[str, Any]:
        """生成月度报告"""
        try:
            # 获取月度数据
            summary = self.finance_manager.get_summary(user_id, year, month)
            records = self.finance_manager.get_user_records(
                user_id, 
                f"{year}-{month:02d}-01", 
                f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
            )
            
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
            
            # 生成报告内容
            report_content = {
                'summary': summary,
                'category_stats': category_stats,
                'top_expenses': sorted(
                    [r for r in records if r['type'] == 'expense'],
                    key=lambda x: x['amount'],
                    reverse=True
                )[:5],
                'top_incomes': sorted(
                    [r for r in records if r['type'] == 'income'],
                    key=lambda x: x['amount'],
                    reverse=True
                )[:5],
                'records_count': len(records)
            }
            
            # 保存报告
            report_title = f"{year}年{month}月财务报告"
            self.save_report(user_id, 'monthly', f"{year}-{month:02d}", report_title, report_content)
            
            return {
                'success': True,
                'report': report_content,
                'message': '月度报告生成成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'生成月度报告失败: {str(e)}'}
    
    def generate_yearly_report(self, user_id: int, year: int) -> Dict[str, Any]:
        """生成年度报告"""
        try:
            # 获取年度数据
            monthly_data = []
            yearly_income = 0
            yearly_expense = 0
            
            for month in range(1, 13):
                monthly_summary = self.finance_manager.get_summary(user_id, year, month)
                monthly_data.append({
                    'month': f"{year}-{month:02d}",
                    'income': monthly_summary['income'],
                    'expense': monthly_summary['expense'],
                    'balance': monthly_summary['balance']
                })
                yearly_income += monthly_summary['income']
                yearly_expense += monthly_summary['expense']
            
            # 获取全年记录进行详细分析
            yearly_records = self.finance_manager.get_user_records(
                user_id, 
                f"{year}-01-01", 
                f"{year}-12-31"
            )
            
            # 分类统计
            category_stats = {}
            for record in yearly_records:
                category = record['category']
                if category not in category_stats:
                    category_stats[category] = {'income': 0, 'expense': 0}
                
                if record['type'] == 'income':
                    category_stats[category]['income'] += record['amount']
                else:
                    category_stats[category]['expense'] += record['amount']
            
            # 月度趋势分析
            monthly_trend = monthly_data
            
            # 生成报告内容
            report_content = {
                'summary': {
                    'income': yearly_income,
                    'expense': yearly_expense,
                    'balance': yearly_income - yearly_expense,
                    'records_count': len(yearly_records)
                },
                'category_stats': category_stats,
                'monthly_trend': monthly_trend,
                'top_expenses': sorted(
                    [r for r in yearly_records if r['type'] == 'expense'],
                    key=lambda x: x['amount'],
                    reverse=True
                )[:10],
                'top_incomes': sorted(
                    [r for r in yearly_records if r['type'] == 'income'],
                    key=lambda x: x['amount'],
                    reverse=True
                )[:10],
                'monthly_analysis': monthly_data
            }
            
            # 保存报告
            report_title = f"{year}年度财务报告"
            self.save_report(user_id, 'yearly', f"{year}", report_title, report_content)
            
            return {
                'success': True,
                'report': report_content,
                'message': '年度报告生成成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'生成年度报告失败: {str(e)}'}
    
    def save_report(self, user_id: int, report_type: str, period: str, title: str, content: Dict[str, Any]):
        """保存报告"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            generated_at = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO reports (user_id, report_type, period, title, content, generated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, report_type, period, title, json.dumps(content, ensure_ascii=False), generated_at))
            
            conn.commit()
        except Exception as e:
            print(f"保存报告失败: {e}")
        finally:
            conn.close()
    
    def get_user_reports(self, user_id: int, report_type: str = None) -> List[Dict[str, Any]]:
        """获取用户报告列表"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT id, report_type, period, title, generated_at FROM reports WHERE user_id = ?'
            params = [user_id]
            
            if report_type:
                query += ' AND report_type = ?'
                params.append(report_type)
            
            query += ' ORDER BY generated_at DESC'
            
            cursor.execute(query, params)
            reports = []
            
            for row in cursor.fetchall():
                reports.append({
                    'id': row[0],
                    'report_type': row[1],
                    'period': row[2],
                    'title': row[3],
                    'generated_at': row[4]
                })
            
            return reports
        except Exception as e:
            print(f"获取报告列表失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_report_content(self, user_id: int, report_id: int) -> Dict[str, Any]:
        """获取报告内容"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT content FROM reports WHERE id = ? AND user_id = ?
            ''', (report_id, user_id))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            else:
                return {}
        except Exception as e:
            print(f"获取报告内容失败: {e}")
            return {}
        finally:
            conn.close()

class AnalysisManager:
    """数据分析管理器"""
    
    def __init__(self, db_manager, finance_manager):
        self.db_manager = db_manager
        self.finance_manager = finance_manager
    
    def get_time_analysis(self, user_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取时间范围分析"""
        try:
            records = self.finance_manager.get_user_records(user_id, start_date, end_date)
            
            # 按日期分组
            daily_data = {}
            for record in records:
                date_key = record['date'][:10]  # 只取日期部分
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
            
            return {
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
                    'incomes': sorted(
                        [r for r in records if r['type'] == 'income'],
                        key=lambda x: x['amount'],
                        reverse=True
                    )[:10],
                    'expenses': sorted(
                        [r for r in records if r['type'] == 'expense'],
                        key=lambda x: x['amount'],
                        reverse=True
                    )[:10]
                }
            }
        except Exception as e:
            return {'success': False, 'message': f'分析失败: {str(e)}'}
    
    def get_category_analysis(self, user_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取分类分析"""
        try:
            records = self.finance_manager.get_user_records(user_id, start_date, end_date)
            
            # 分类统计
            category_stats = {}
            for record in records:
                category = record['category']
                if category not in category_stats:
                    category_stats[category] = {
                        'income': 0,
                        'expense': 0,
                        'count': 0,
                        'records': []
                    }
                
                category_stats[category]['records'].append(record)
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
            
            return {
                'success': True,
                'category_stats': category_stats,
                'summary': {
                    'total_income': total_income,
                    'total_expense': total_expense,
                    'balance': total_income - total_expense
                }
            }
        except Exception as e:
            return {'success': False, 'message': f'分类分析失败: {str(e)}'}

class SyncManager:
    """同步管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def sync_records(self, user_id: int, device_id: str, client_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """同步记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取服务器端记录
            server_records = {}
            cursor.execute('''
                SELECT sync_id, amount, category, record_type, description, record_date, updated_at
                FROM finance_records WHERE user_id = ?
            ''', (user_id,))
            
            for row in cursor.fetchall():
                server_records[row[0]] = {
                    'amount': row[1],
                    'category': row[2],
                    'type': row[3],
                    'description': row[4],
                    'date': row[5],
                    'updated_at': row[6]
                }
            
            # 处理同步
            conflicts = []
            new_records = []
            updated_records = []
            
            for client_record in client_records:
                sync_id = client_record.get('sync_id')
                
                if sync_id in server_records:
                    # 记录已存在，检查是否需要更新
                    server_record = server_records[sync_id]
                    if client_record.get('updated_at', '') > server_record['updated_at']:
                        # 客户端版本更新
                        cursor.execute('''
                            UPDATE finance_records 
                            SET amount=?, category=?, record_type=?, description=?, record_date=?, updated_at=?
                            WHERE sync_id=? AND user_id=?
                        ''', (
                            client_record['amount'],
                            client_record['category'],
                            client_record['type'],
                            client_record.get('description', ''),
                            client_record.get('date', ''),
                            client_record.get('updated_at', ''),
                            sync_id,
                            user_id
                        ))
                        updated_records.append(sync_id)
                else:
                    # 新记录
                    new_sync_id = secrets.token_hex(16)
                    created_at = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    cursor.execute('''
                        INSERT INTO finance_records 
                        (user_id, amount, category, record_type, description, record_date, created_at, updated_at, sync_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        client_record['amount'],
                        client_record['category'],
                        client_record['type'],
                        client_record.get('description', ''),
                        client_record.get('date', created_at),
                        created_at,
                        created_at,
                        new_sync_id
                    ))
                    new_records.append(new_sync_id)
            
            # 更新同步记录
            sync_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT OR REPLACE INTO sync_records (user_id, device_id, last_sync_time, sync_count)
                VALUES (?, ?, ?, COALESCE((SELECT sync_count FROM sync_records WHERE user_id=? AND device_id=?), 0) + 1)
            ''', (user_id, device_id, sync_time, user_id, device_id))
            
            conn.commit()
            
            return {
                'success': True,
                'new_records': new_records,
                'updated_records': updated_records,
                'conflicts': conflicts,
                'server_records': self.get_server_records_for_sync(user_id),
                'message': '同步完成'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()
    
    def get_server_records_for_sync(self, user_id: int) -> List[Dict[str, Any]]:
        """获取服务器端记录用于同步"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT sync_id, amount, category, record_type, description, record_date, updated_at
                FROM finance_records WHERE user_id = ?
            ''', (user_id,))
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'sync_id': row[0],
                    'amount': row[1],
                    'category': row[2],
                    'type': row[3],
                    'description': row[4],
                    'date': row[5],
                    'updated_at': row[6]
                })
            
            return records
        except Exception as e:
            print(f"获取同步记录失败: {e}")
            return []
        finally:
            conn.close()

# 全局管理器实例
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
finance_manager = FinanceManager(db_manager)
report_manager = ReportManager(db_manager, finance_manager)
analysis_manager = AnalysisManager(db_manager, finance_manager)
sync_manager = SyncManager(db_manager)

# 辅助函数
def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    sync_token = request.headers.get('X-Sync-Token')
    
    if user_id:
        return {'user_id': user_id, 'source': 'session'}
    elif sync_token:
        result = user_manager.get_user_by_token(sync_token)
        if result['success']:
            return {'user_id': result['user_id'], 'source': 'token'}
    
    return None

# 用户认证API
@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        result = user_manager.register_user(username, password, email)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        result = user_manager.authenticate_user(username, password)
        if result['success']:
            session['user_id'] = result['user_id']
            session['username'] = username
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': '登出成功'})

@app.route('/api/auth/status')
def auth_status():
    """获取认证状态"""
    current_user = get_current_user()
    if current_user:
        return jsonify({
            'logged_in': True,
            'user_id': current_user['user_id']
        })
    else:
        return jsonify({'logged_in': False})

# 财务记录API
@app.route('/api/records', methods=['GET'])
def get_records():
    """获取所有记录"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        records = finance_manager.get_user_records(current_user['user_id'])
        return jsonify(records)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/records', methods=['POST'])
def add_record():
    """添加新记录"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        data = request.get_json()
        result = finance_manager.add_record(current_user['user_id'], data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除记录"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        result = finance_manager.delete_record(current_user['user_id'], record_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/summary')
def get_summary():
    """获取汇总数据"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        summary = finance_manager.get_summary(current_user['user_id'])
        return jsonify(summary)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/monthly-data')
def get_monthly_data():
    """获取月度数据"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        year = request.args.get('year', type=int)
        monthly_data = finance_manager.get_monthly_data(current_user['user_id'], year)
        return jsonify(monthly_data)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/categories')
def get_categories():
    """获取分类列表"""
    return jsonify(finance_manager.categories)

# 同步API
@app.route('/api/sync', methods=['POST'])
def sync_data():
    """数据同步"""
    sync_token = request.headers.get('X-Sync-Token')
    if not sync_token:
        return jsonify({'success': False, 'message': '缺少同步令牌'}), 401
    
    user_result = user_manager.get_user_by_token(sync_token)
    if not user_result['success']:
        return jsonify({'success': False, 'message': '无效的同步令牌'}), 401
    
    try:
        data = request.get_json()
        device_id = data.get('device_id', 'unknown')
        client_records = data.get('records', [])
        
        result = sync_manager.sync_records(
            user_result['user_id'], 
            device_id, 
            client_records
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/sync/records')
def get_sync_records():
    """获取同步记录"""
    sync_token = request.headers.get('X-Sync-Token')
    if not sync_token:
        return jsonify({'success': False, 'message': '缺少同步令牌'}), 401
    
    user_result = user_manager.get_user_by_token(sync_token)
    if not user_result['success']:
        return jsonify({'success': False, 'message': '无效的同步令牌'}), 401
    
    try:
        records = sync_manager.get_server_records_for_sync(user_result['user_id'])
        return jsonify(records)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# 报告生成API
@app.route('/api/reports/monthly', methods=['POST'])
def generate_monthly_report():
    """生成月度报告"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        data = request.get_json()
        year = data.get('year', dt.now().year)
        month = data.get('month', dt.now().month)
        
        result = report_manager.generate_monthly_report(current_user['user_id'], year, month)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/reports/yearly', methods=['POST'])
def generate_yearly_report():
    """生成年度报告"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        data = request.get_json()
        year = data.get('year', dt.now().year)
        
        result = report_manager.generate_yearly_report(current_user['user_id'], year)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/reports')
def get_reports():
    """获取报告列表"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        report_type = request.args.get('type')
        reports = report_manager.get_user_reports(current_user['user_id'], report_type)
        return jsonify(reports)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/reports/<int:report_id>')
def get_report_content(report_id):
    """获取报告内容"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        content = report_manager.get_report_content(current_user['user_id'], report_id)
        return jsonify(content)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# 数据分析API
@app.route('/api/analysis/time-range')
def get_time_analysis():
    """获取时间范围分析"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'message': '请提供开始日期和结束日期'}), 400
        
        result = analysis_manager.get_time_analysis(current_user['user_id'], start_date, end_date)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/analysis/category')
def get_category_analysis():
    """获取分类分析"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'message': '请提供开始日期和结束日期'}), 400
        
        result = analysis_manager.get_category_analysis(current_user['user_id'], start_date, end_date)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# 自动报告生成任务
def auto_generate_reports():
    """自动生成月度报告和年度报告"""
    while True:
        try:
            now = dt.now()
            
            # 每月1日凌晨1点生成上月报告
            if now.day == 1 and now.hour == 1:
                last_month = now.month - 1 if now.month > 1 else 12
                last_year = now.year if now.month > 1 else now.year - 1
                
                # 获取所有用户
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM users')
                users = cursor.fetchall()
                conn.close()
                
                for user_row in users:
                    user_id = user_row[0]
                    report_manager.generate_monthly_report(user_id, last_year, last_month)
            
            # 每年1月1日凌晨2点生成上年报告
            if now.month == 1 and now.day == 1 and now.hour == 2:
                last_year = now.year - 1
                
                # 获取所有用户
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM users')
                users = cursor.fetchall()
                conn.close()
                
                for user_row in users:
                    user_id = user_row[0]
                    report_manager.generate_yearly_report(user_id, last_year)
            
            # 每小时检查一次
            threading.Event().wait(3600)
            
        except Exception as e:
            print(f"自动报告生成失败: {e}")
            threading.Event().wait(3600)  # 出错后等待1小时再重试

# 启动自动报告生成任务
report_thread = threading.Thread(target=auto_generate_reports, daemon=True)
report_thread.start()

if __name__ == '__main__':
    print("双端记账系统后端API服务启动中...")
    print("访问地址: http://127.0.0.1:5001")
    print("API文档: http://127.0.0.1:5001/api/docs")
    app.run(debug=True, host='127.0.0.1', port=5001)
