from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 初始化数据库
 db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    @property
    def password(self):
        """密码属性（只读）"""
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

class DataSource(db.Model):
    """数据源模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # web, api, file
    url = db.Column(db.String(500), nullable=True)
    config = db.Column(db.Text, nullable=True)  # JSON配置
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrawledData(db.Model):
    """爬取数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=True)
    metadata = db.Column(db.Text, nullable=True)  # JSON元数据
    crawled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    source = db.relationship('DataSource', backref=db.backref('crawled_data', lazy=True))

class AnalysisResult(db.Model):
    """分析结果模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # report, chart, model
    content = db.Column(db.Text, nullable=False)  # JSON内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Task(db.Model):
    """任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # crawl, analyze
    status = db.Column(db.String(50), nullable=False)  # pending, running, completed, failed
    config = db.Column(db.Text, nullable=True)  # JSON配置
    result = db.Column(db.Text, nullable=True)  # JSON结果
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 初始化数据库
 def init_db(app):
    """初始化数据库"""
    with app.app_context():
        db.create_all()