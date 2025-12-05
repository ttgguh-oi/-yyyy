import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'  # 密钥
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://root:password@localhost/observatory_db'  # MySQL配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件存储路径
    DATA_STORAGE_PATH = os.environ.get('DATA_STORAGE_PATH') or 'data/'
    
    # API配置
    API_TIMEOUT = 30
    
    # 其他配置
    DEBUG = True
    TESTING = False

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# 测试环境配置
class TestingConfig(Config):
    TESTING = True

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}