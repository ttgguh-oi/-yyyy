from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config
from models import db, User, init_db
import os

# 创建应用工厂函数
def create_app(config_name='default'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建数据存储目录
    if not os.path.exists(app.config['DATA_STORAGE_PATH']):
        os.makedirs(app.config['DATA_STORAGE_PATH'])
    
    # 初始化登录管理器
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    @login_manager.user_loader
    def load_user(user_id):
        """加载用户"""
        return User.query.get(int(user_id))
    
    # 注册蓝图
    from auth import auth_bp
    from dashboard import dashboard_bp
    from crawler import crawler_bp
    from analyzer import analyzer_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(crawler_bp, url_prefix='/crawler')
    app.register_blueprint(analyzer_bp, url_prefix='/analyzer')
    
    # 主页路由
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')
    
    # 404处理
    @app.errorhandler(404)
    def page_not_found(error):
        """404页面"""
        return render_template('404.html'), 404
    
    # 500处理
    @app.errorhandler(500)
    def internal_server_error(error):
        """500页面"""
        return render_template('500.html'), 500
    
    return app

# 主函数
if __name__ == '__main__':
    # 创建应用
    app = create_app('development')
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)