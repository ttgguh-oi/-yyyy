# 智能瞭望系统 (Intelligent Observatory System)

智能瞭望系统是一个集数据抓取、存储、清洗和分析于一体的综合性数据平台，帮助用户实现多源数据的快速获取和智能分析。

## 功能特点

### 1. 用户认证
- 用户注册与登录
- 会话管理
- 权限控制

### 2. 多源数据抓取
- **网页爬虫**：支持通过CSS选择器抓取网页内容
- **API接口**：支持调用RESTful API获取结构化数据
- **本地文件**：支持读取CSV、JSON等格式的本地文件

### 3. 数据存储
- 使用SQLAlchemy支持多种数据库（默认SQLite，可配置MySQL）
- 数据统一存储，便于管理和查询

### 4. 数据处理与分析
- 数据清洗：去重、过滤、标准化
- 文本分析：词频统计、关键词提取
- 情感分析：文本情感倾向判断
- 主题建模：自动识别文本主题
- 分类分析：基于机器学习的文本分类

## 技术栈

- **后端框架**：Flask
- **数据库**：SQLAlchemy (支持SQLite/MySQL)
- **数据处理**：Pandas
- **机器学习**：scikit-learn
- **文本分析**：jieba (中文分词)
- **网络请求**：requests
- **网页解析**：BeautifulSoup4
- **用户界面**：Bootstrap 5

## 安装与配置

### 1. 环境要求
- Python 3.7+
- pip

### 2. 安装依赖
```bash
cd intelligent_observatory
pip install -r requirements.txt
```

### 3. 配置文件
编辑 `config.py` 文件，根据实际情况修改配置：

```python
# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///observatory.db'  # 默认使用SQLite
# 或使用MySQL
# SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/observatory'

# 文件存储路径
FILE_STORAGE_PATH = 'uploads/'

# 其他配置...
```

### 4. 初始化数据库
```bash
python -c "from app import create_app; from models import db; app = create_app(); with app.app_context(): db.create_all()"
```

## 使用方法

### 1. 启动应用
```bash
python app.py
```

应用将在 `http://127.0.0.1:5000` 启动。

### 2. 基本操作

#### 2.1 用户注册与登录
- 访问首页点击"注册"按钮创建新用户
- 使用注册的用户名和密码登录系统

#### 2.2 添加数据源
1. 登录后点击左侧菜单"数据抓取"
2. 点击"添加数据源"按钮
3. 填写数据源信息：
   - 名称：数据源的标识
   - 类型：选择网页、API或本地文件
   - URL/文件路径：根据类型填写
   - 配置：JSON格式的详细配置

#### 2.3 抓取数据
1. 在数据源列表中点击"爬取"按钮
2. 等待爬取完成
3. 点击"查看数据"查看抓取结果

#### 2.4 数据清洗与分析
1. 点击左侧菜单"数据分析"
2. 选择数据清洗选项，点击"开始清洗"
3. 选择分析类型，点击"开始分析"
4. 在"最近分析结果"中查看分析结果

## 数据源配置示例

### 1. 网页爬虫配置
```json
{
  "selector": ".article",        // 文章容器选择器
  "title_selector": "h2",        // 标题选择器
  "content_selector": ".content" // 内容选择器
}
```

### 2. API接口配置
```json
{
  "method": "GET",                  // 请求方法
  "headers": {                      // 请求头
    "Authorization": "Bearer token"
  },
  "params": {                       // 请求参数
    "page": 1,
    "limit": 100
  },
  "items_key": "data.items",       // 数据路径
  "title_path": "title",           // 标题路径
  "content_path": "description"    // 内容路径
}
```

### 3. 本地文件配置
```json
{
  "file_type": "csv",              // 文件类型
  "title_column": "title",         // 标题列名
  "content_column": "content"      // 内容列名
}
```

## 项目结构

```
intelligent_observatory/
├── app.py                 # 应用主入口
├── config.py              # 配置文件
├── models.py              # 数据模型
├── auth.py                # 认证模块
├── dashboard.py           # 仪表盘模块
├── crawler.py             # 数据抓取模块
├── analyzer.py            # 数据分析模块
├── requirements.txt       # 依赖列表
├── templates/             # HTML模板
│   ├── base.html          # 基础模板
│   ├── index.html         # 首页
│   ├── auth/              # 认证模板
│   ├── dashboard/         # 仪表盘模板
│   ├── crawler/           # 爬虫模板
│   └── analyzer/          # 分析模板
├── static/                # 静态资源
└── uploads/               # 文件上传目录
```

## 开发说明

### 1. 添加新功能
- 在对应的模块文件中添加路由和功能
- 创建对应的模板文件
- 如需添加新模型，在models.py中定义

### 2. 运行测试
```bash
# 暂未实现测试套件
```

### 3. 部署到生产环境
- 使用Gunicorn或uWSGI作为WSGI服务器
- 配置Nginx或Apache作为反向代理
- 设置DEBUG=False
- 配置数据库连接

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系：

- 项目维护者：[Your Name]
- Email：[your.email@example.com]
- GitHub：[your-github-repo]
