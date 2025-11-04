# 双端记账系统

一个支持Web端和移动端数据互通的个人记账系统，具有多用户登录、数据同步、报告分析等功能。

## 🚀 系统特性

### 核心功能
- ✅ **多用户登录系统** - 支持用户注册、登录、会话管理
- ✅ **财务记录管理** - 收入/支出记录添加、查看、删除
- ✅ **数据统计分析** - 月度/年度数据汇总、分类分析
- ✅ **自动报告生成** - 月度报告、年度报告自动生成
- ✅ **移动端数据同步** - 支持移动端与Web端数据实时同步
- ✅ **可视化图表展示** - 使用ECharts展示财务数据图表
- ✅ **实时数据更新** - 自动刷新和实时数据展示

### 技术特性
- **前后端分离架构** - Flask后端 + 原生JavaScript前端
- **RESTful API设计** - 标准化的API接口
- **SQLite数据库** - 轻量级数据存储
- **响应式设计** - 支持PC和移动端访问
- **数据安全** - 密码哈希加密、会话管理

## 📁 项目结构

```
Finance/
├── backend_api.py          # 后端API服务
├── web_app.py              # Web应用
├── start_system.py         # 系统启动脚本
├── README.md               # 项目文档
├── finance_system.db       # 数据库文件（自动生成）
└── templates/              # HTML模板
    ├── login.html          # 登录页面
    ├── register.html       # 注册页面
    ├── dashboard.html      # 仪表板页面
    └── reports.html        # 报告分析页面
```

## 🛠️ 快速开始

### 环境要求
- Python 3.7+
- Flask
- requests
- sqlite3 (Python内置)

### 安装依赖
```bash
pip install flask requests
```

### 启动系统
```bash
cd Finance
python start_system.py
```

### 访问系统
- **Web端**: http://127.0.0.1:5000
- **后端API**: http://127.0.0.1:5001

### 测试账号
- 用户名: `testuser`
- 密码: `test123`

## 📊 系统架构

### 后端架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web应用       │    │   后端API       │    │   数据库        │
│  (端口:5000)    │◄──►│   (端口:5001)   │◄──►│   SQLite        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 数据库设计
```sql
-- 用户表
users (id, username, password_hash, email, created_at, last_login, sync_token)

-- 财务记录表  
finance_records (id, user_id, amount, category, record_type, description, record_date, created_at, updated_at, sync_id)

-- 同步记录表
sync_records (id, user_id, device_id, last_sync_time, sync_count)

-- 报告表
reports (id, user_id, report_type, period, title, content, generated_at)

-- 分析数据表
analysis_data (id, user_id, data_type, period, data_content, created_at)
```

## 🔧 API接口文档

### 用户认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录  
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/status` - 认证状态

### 财务记录
- `GET /api/records` - 获取记录列表
- `POST /api/records` - 添加新记录
- `DELETE /api/records/{id}` - 删除记录

### 数据统计
- `GET /api/summary` - 获取汇总数据
- `GET /api/monthly-data` - 获取月度数据
- `GET /api/categories` - 获取分类列表

### 报告生成
- `POST /api/reports/monthly` - 生成月度报告
- `POST /api/reports/yearly` - 生成年度报告
- `GET /api/reports` - 获取报告列表
- `GET /api/reports/{id}` - 获取报告内容

### 数据分析
- `GET /api/analysis/time-range` - 时间范围分析
- `GET /api/analysis/category` - 分类分析

### 数据同步
- `POST /api/sync` - 数据同步
- `GET /api/sync/records` - 获取同步记录

## 📱 移动端集成

### 移动端特性
- React Native应用
- 离线数据存储
- 自动数据同步
- 本地推送通知

### 同步机制
1. 移动端使用同步令牌认证
2. 增量数据同步
3. 冲突检测和解决
4. 同步状态跟踪

## 🎯 使用指南

### 1. 用户注册和登录
- 访问Web端注册新用户
- 使用用户名密码登录
- 系统自动生成同步令牌

### 2. 记录管理
- 在仪表板添加收入/支出记录
- 选择分类和填写描述
- 查看历史记录和统计数据

### 3. 报告分析
- 生成月度/年度财务报告
- 查看分类统计和趋势图表
- 分析大额收支记录

### 4. 数据同步
- 移动端使用同步令牌连接
- 自动同步财务记录
- 支持多设备数据一致性

## 🔒 安全特性

- **密码安全**: SHA-256哈希加密
- **会话管理**: Flask会话机制
- **数据验证**: 输入数据验证和清理
- **API保护**: 认证和授权检查

## 📈 扩展功能

### 已实现功能
- [x] 基础记账功能
- [x] 多用户支持
- [x] 数据同步
- [x] 报告生成
- [x] 可视化图表

### 计划功能
- [ ] 预算管理
- [ ] 账单提醒
- [ ] 数据导出
- [ ] 多币种支持
- [ ] 投资跟踪

## 🐛 故障排除

### 常见问题

**1. 服务启动失败**
```bash
# 检查端口占用
netstat -ano | findstr :5000
netstat -ano | findstr :5001

# 检查依赖
pip list | grep flask
pip list | grep requests
```

**2. 数据库问题**
```bash
# 删除数据库重新启动
rm finance_system.db
python start_system.py
```

**3. 同步问题**
- 检查网络连接
- 验证同步令牌
- 查看同步记录

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 项目仓库: [GitHub Repository]
- 邮箱: [your-email@example.com]

---

**双端记账系统** - 让财务管理更简单、更智能！
