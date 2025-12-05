from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from models import db, User

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        # 获取表单数据
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 表单验证
        if not username or not password or not confirm_password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.register'))
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))
        
        # 创建新用户
        new_user = User(username=username)
        new_user.password = password  # 使用密码哈希
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        # 获取表单数据
        username = request.form['username']
        password = request.form['password']
        
        # 表单验证
        if not username or not password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('auth.login'))
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 验证用户和密码
        if user and user.verify_password(password):
            login_user(user)
            flash('登录成功', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('index'))