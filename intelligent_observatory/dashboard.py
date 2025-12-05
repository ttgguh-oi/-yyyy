from flask import Blueprint, render_template, flash
from flask_login import login_required
from models import db, DataSource, CrawledData, AnalysisResult, Task

# 创建仪表盘蓝图
dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

@dashboard_bp.route('/')
@login_required
def index():
    """仪表盘主页"""
    try:
        # 获取统计数据
        total_sources = DataSource.query.count()
        total_crawled_data = CrawledData.query.count()
        total_analysis_results = AnalysisResult.query.count()
        
        # 获取最近的数据源
        recent_sources = DataSource.query.order_by(DataSource.created_at.desc()).limit(5).all()
        
        # 获取最近的爬取数据
        recent_crawled_data = CrawledData.query.order_by(CrawledData.crawled_at.desc()).limit(5).all()
        
        # 获取最近的分析结果
        recent_analysis_results = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).limit(5).all()
        
        # 获取任务状态
        pending_tasks = Task.query.filter_by(status='pending').count()
        running_tasks = Task.query.filter_by(status='running').count()
        completed_tasks = Task.query.filter_by(status='completed').count()
        failed_tasks = Task.query.filter_by(status='failed').count()
        
        # 构建上下文数据
        context = {
            'total_sources': total_sources,
            'total_crawled_data': total_crawled_data,
            'total_analysis_results': total_analysis_results,
            'recent_sources': recent_sources,
            'recent_crawled_data': recent_crawled_data,
            'recent_analysis_results': recent_analysis_results,
            'task_status': {
                'pending': pending_tasks,
                'running': running_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks
            }
        }
        
        return render_template('dashboard/index.html', **context)
        
    except Exception as e:
        flash(f'获取仪表盘数据失败: {str(e)}', 'danger')
        return render_template('dashboard/index.html')

@dashboard_bp.route('/stats')
@login_required
def stats():
    """统计信息页面"""
    try:
        # 获取数据源类型统计
        sources_by_type = db.session.query(DataSource.type, db.func.count(DataSource.id))\
                                    .group_by(DataSource.type)\
                                    .all()
        
        # 获取爬取数据按来源统计
        crawled_data_by_source = db.session.query(DataSource.name, db.func.count(CrawledData.id))\
                                          .join(CrawledData, DataSource.id == CrawledData.source_id)\
                                          .group_by(DataSource.name)\
                                          .order_by(db.func.count(CrawledData.id).desc())\
                                          .limit(10)\
                                          .all()
        
        # 构建上下文数据
        context = {
            'sources_by_type': sources_by_type,
            'crawled_data_by_source': crawled_data_by_source
        }
        
        return render_template('dashboard/stats.html', **context)
        
    except Exception as e:
        flash(f'获取统计数据失败: {str(e)}', 'danger')
        return render_template('dashboard/stats.html')

@dashboard_bp.route('/settings')
@login_required
def settings():
    """系统设置页面"""
    return render_template('dashboard/settings.html')