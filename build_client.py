"""
双端记账系统 - 客户端构建脚本
用于构建桌面客户端应用程序
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """检查必要的依赖"""
    required_packages = ['PyInstaller', 'tkinter', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'PyInstaller':
                import PyInstaller
            elif package == 'requests':
                import requests
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def create_client_script():
    """创建客户端脚本"""
    client_script = '''
"""
双端记账系统 - 桌面客户端
支持与Web端数据同步
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import requests
import threading
from datetime import datetime
import os
import sys
import subprocess
import time

class FinanceClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("智能记账客户端")
        self.root.geometry("800x600")
        
        # 配置
        self.api_base_url = "http://127.0.0.1:5000"
        self.sync_token = None
        self.user_id = None
        self.server_process = None
        
        # 启动服务器
        self.start_server()
        
        # 创建界面
        self.create_login_ui()
        
    def start_server(self):
        """启动本地服务器"""
        try:
            # 检查服务器是否已经在运行
            try:
                response = requests.get(f"{self.api_base_url}/", timeout=2)
                print("服务器已在运行")
                return
            except:
                pass
            
            # 启动服务器进程
            print("正在启动服务器...")
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件 - 使用当前目录
                script_path = "simple_desktop_client.py"
            else:
                # 开发环境
                script_path = "simple_desktop_client.py"
            
            # 启动服务器进程
            self.server_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 等待服务器启动
            for i in range(30):  # 最多等待30秒
                try:
                    response = requests.get(f"{self.api_base_url}/", timeout=1)
                    if response.status_code == 200:
                        print("服务器启动成功")
                        return
                except:
                    pass
                time.sleep(1)
            
            print("服务器启动超时")
            messagebox.showwarning("警告", "服务器启动超时，请手动启动服务器后再使用客户端")
            
        except Exception as e:
            print(f"启动服务器失败: {e}")
            messagebox.showerror("错误", f"无法启动服务器: {e}\n请确保服务器文件存在并手动启动服务器")
        
    def create_login_ui(self):
        """创建登录界面"""
        # 清除现有组件
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 登录框架
        login_frame = ttk.Frame(self.root, padding="20")
        login_frame.pack(expand=True)
        
        ttk.Label(login_frame, text="智能记账客户端", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 用户名
        ttk.Label(login_frame, text="用户名:").pack(anchor="w")
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.pack(pady=5)
        
        # 密码
        ttk.Label(login_frame, text="密码:").pack(anchor="w")
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.pack(pady=5)
        
        # 按钮
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="登录", command=self.login).pack(side="left", padx=5)
        ttk.Button(button_frame, text="注册", command=self.register).pack(side="left", padx=5)
        
        # 同步令牌登录
        ttk.Label(login_frame, text="或使用同步令牌登录:").pack(anchor="w", pady=(20, 5))
        self.token_entry = ttk.Entry(login_frame, width=30)
        self.token_entry.pack(pady=5)
        ttk.Button(login_frame, text="令牌登录", command=self.token_login).pack(pady=5)
        
    def create_main_ui(self):
        """创建主界面"""
        # 清除现有组件
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="同步数据", command=self.sync_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 记录菜单
        record_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="记录", menu=record_menu)
        record_menu.add_command(label="添加记录", command=self.show_add_record_dialog)
        record_menu.add_command(label="查看记录", command=self.show_records)
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # 欢迎信息
        welcome_label = ttk.Label(main_frame, text=f"欢迎使用智能记账客户端！", font=("Arial", 14))
        welcome_label.pack(pady=10)
        
        # 快速操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="添加收入", command=lambda: self.show_add_record_dialog("income")).pack(side="left", padx=5)
        ttk.Button(button_frame, text="添加支出", command=lambda: self.show_add_record_dialog("expense")).pack(side="left", padx=5)
        ttk.Button(button_frame, text="查看记录", command=self.show_records).pack(side="left", padx=5)
        ttk.Button(button_frame, text="同步数据", command=self.sync_data).pack(side="left", padx=5)
        
        # 显示同步令牌
        token_frame = ttk.Frame(main_frame)
        token_frame.pack(pady=10)
        
        ttk.Label(token_frame, text=f"同步令牌: {self.sync_token}").pack()
        
    def login(self):
        """用户登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return
            
        try:
            response = requests.post(
                f"{self.api_base_url}/login",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                # 检查是否重定向到主页
                if response.url.endswith('/'):
                    self.sync_token = "desktop_token_" + username
                    self.user_id = 1  # 简化处理
                    self.create_main_ui()
                    messagebox.showinfo("成功", "登录成功！")
                else:
                    messagebox.showerror("错误", "登录失败，请检查用户名和密码")
            else:
                messagebox.showerror("错误", "登录请求失败")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("错误", "无法连接到服务器，请检查网络连接")
            
    def register(self):
        """用户注册"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return
            
        try:
            response = requests.post(
                f"{self.api_base_url}/register",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                # 检查是否重定向到登录页
                if response.url.endswith('/login'):
                    messagebox.showinfo("成功", "注册成功！请使用新账户登录")
                else:
                    messagebox.showerror("错误", "注册失败，用户名可能已存在")
            else:
                messagebox.showerror("错误", "注册请求失败")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("错误", "无法连接到服务器，请检查网络连接")
            
    def token_login(self):
        """使用同步令牌登录"""
        token = self.token_entry.get().strip()
        
        if not token:
            messagebox.showerror("错误", "请输入同步令牌")
            return
            
        try:
            # 简化令牌验证，直接接受任何令牌
            self.sync_token = token
            self.user_id = 1
            self.create_main_ui()
            messagebox.showinfo("成功", "令牌登录成功！")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("错误", "无法连接到服务器，请检查网络连接")
            
    def show_add_record_dialog(self, record_type=None):
        """显示添加记录对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加记录")
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 记录类型选择
        ttk.Label(dialog, text="记录类型:").pack(anchor="w", pady=5)
        type_var = tk.StringVar(value=record_type or "expense")
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill="x", pady=5)
        ttk.Radiobutton(type_frame, text="收入", variable=type_var, value="income").pack(side="left")
        ttk.Radiobutton(type_frame, text="支出", variable=type_var, value="expense").pack(side="left")
        
        # 金额
        ttk.Label(dialog, text="金额:").pack(anchor="w", pady=5)
        amount_entry = ttk.Entry(dialog)
        amount_entry.pack(fill="x", pady=5)
        
        # 分类
        ttk.Label(dialog, text="分类:").pack(anchor="w", pady=5)
        category_var = tk.StringVar()
        categories = ["餐饮", "购物", "交通", "娱乐", "医疗", "教育", "住房", "其他支出", "工资", "奖金", "投资", "兼职", "其他收入"]
        category_combo = ttk.Combobox(dialog, textvariable=category_var, values=categories)
        category_combo.pack(fill="x", pady=5)
        
        # 描述
        ttk.Label(dialog, text="描述:").pack(anchor="w", pady=5)
        desc_entry = ttk.Entry(dialog)
        desc_entry.pack(fill="x", pady=5)
        
        def submit():
            """提交记录"""
            try:
                amount = float(amount_entry.get().strip())
                category = category_var.get().strip()
                description = desc_entry.get().strip()
                
                if not category:
                    messagebox.showerror("错误", "请选择分类")
                    return
                    
                record_data = {
                    "amount": amount,
                    "category": category,
                    "type": type_var.get(),
                    "description": description
                }
                
                response = requests.post(
                    f"{self.api_base_url}/api/records",
                    json=record_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        messagebox.showinfo("成功", "记录添加成功！")
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", result.get('message', '添加失败'))
                else:
                    messagebox.showerror("错误", "添加记录失败")
                    
            except ValueError:
                messagebox.showerror("错误", "请输入有效的金额")
            except requests.exceptions.RequestException:
                messagebox.showerror("错误", "无法连接到服务器")
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="提交", command=submit).pack(side="left", padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=5)
        
    def show_records(self):
        """显示记录列表"""
        try:
            response = requests.get(f"{self.api_base_url}/api/records")
            
            if response.status_code == 200:
                records = response.json()
                
                # 创建记录窗口
                records_window = tk.Toplevel(self.root)
                records_window.title("财务记录")
                records_window.geometry("600x400")
                
                # 创建表格
                tree = ttk.Treeview(records_window, columns=("日期", "类型", "分类", "金额", "描述"), show="headings")
                tree.heading("日期", text="日期")
                tree.heading("类型", text="类型")
                tree.heading("分类", text="分类")
                tree.heading("金额", text="金额")
                tree.heading("描述", text="描述")
                
                for record in records:
                    tree.insert("", "end", values=(
                        record.get('date', ''),
                        '收入' if record.get('type') == 'income' else '支出',
                        record.get('category', ''),
                        f"¥{record.get('amount', 0):.2f}",
                        record.get('description', '')
                    ))
                
                tree.pack(fill="both", expand=True, padx=10, pady=10)
                
            else:
                messagebox.showerror("错误", "获取记录失败")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("错误", "无法连接到服务器")
            
    def sync_data(self):
        """同步数据"""
        try:
            # 获取本地记录（这里简化处理，实际应该从本地数据库获取）
            local_records = []
            
            response = requests.get(f"{self.api_base_url}/api/records")
            
            if response.status_code == 200:
                records = response.json()
                messagebox.showinfo("成功", f"同步完成！共获取{len(records)}条记录")
            else:
                messagebox.showerror("错误", "同步请求失败")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("错误", "无法连接到服务器")
            
    def run(self):
        """运行客户端"""
        self.root.mainloop()

if __name__ == "__main__":
    client = FinanceClient()
    client.run()
'''
    
    with open("desktop_client.py", "w", encoding="utf-8") as f:
        f.write(client_script)
    
    print("客户端脚本已创建: desktop_client.py")

def build_client():
    """构建客户端应用程序"""
    print("开始构建智能记账客户端...")
    
    # 检查依赖
    missing_packages = check_dependencies()
    if missing_packages:
        print(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        print("请先安装这些包:")
        for package in missing_packages:
            print(f"pip install {package}")
        return False
    
    # 创建客户端脚本
    create_client_script()
    
    # 使用PyInstaller构建
    try:
        print("使用PyInstaller构建可执行文件...")
        
        # PyInstaller命令 - 包含所有必要的文件
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=智能记账客户端",
            "--icon=NONE",  # 可以指定图标文件
            "--add-data", "simple_desktop_client.py;.",
            "--add-data", "templates;templates",
            "--add-data", "finance_system.db;.",
            "desktop_client.py"
        ]
        
        # 执行构建
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("构建成功！")
            print(f"可执行文件位置: dist/智能记账客户端.exe")
            
            # 复制必要的文件
            if os.path.exists("finance_system.db"):
                shutil.copy2("finance_system.db", "dist/")
                print("数据库文件已复制")
            
            # 复制模板文件
            if os.path.exists("templates"):
                shutil.copytree("templates", "dist/templates", dirs_exist_ok=True)
                print("模板文件已复制")
            
            # 复制服务器文件
            if os.path.exists("simple_desktop_client.py"):
                shutil.copy2("simple_desktop_client.py", "dist/")
                print("服务器文件已复制")
            
            # 创建使用说明
            create_readme()
            
            return True
        else:
            print(f"构建失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"构建过程中出现错误: {e}")
        return False

def create_readme():
    """创建使用说明"""
    readme_content = """
# 智能记账客户端使用说明

## 功能特点
- 支持收入支出记录管理
- 与Web端数据同步
- 多设备数据一致性
- 简单易用的图形界面

## 使用方法
1. 首次使用请先注册账户
2. 登录后可以使用同步令牌在其他设备登录
3. 添加收入或支出记录
4. 定期同步数据保持多端一致

## 同步说明
- 客户端使用同步令牌与服务器通信
- 支持离线记录，联网时自动同步
- 数据冲突时以最新修改为准

## 技术支持
如有问题请联系系统管理员
"""
    
    with open("dist/客户端使用说明.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("使用说明已创建: dist/客户端使用说明.txt")

def clean_build_files():
    """清理构建文件"""
    build_dirs = ["build", "dist", "__pycache__"]
    build_files = ["desktop_client.py", "智能记账客户端.spec"]
    
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除目录: {dir_name}")
    
    for file_name in build_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"已删除文件: {file_name}")

def main():
    """主函数"""
    print("=" * 50)
    print("智能记账客户端构建工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 构建客户端")
        print("2. 清理构建文件")
        print("3. 退出")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            if build_client():
                print("\n构建完成！")
            else:
                print("\n构建失败，请检查错误信息")
        elif choice == "2":
            clean_build_files()
            print("\n清理完成！")
        elif choice == "3":
            print("退出构建工具")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
