from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
import requests
from bs4 import BeautifulSoup
import json
import csv
import os
from datetime import datetime
from models import db, DataSource, CrawledData
from config import Config

# 创建爬虫蓝图
crawler_bp = Blueprint('crawler', __name__, template_folder='templates')

@crawler_bp.route('/')
@login_required
def index():
    """爬虫主页"""
    try:
        # 获取所有数据源
        data_sources = DataSource.query.all()
        return render_template('crawler/index.html', data_sources=data_sources)
    except Exception as e:
        flash(f'获取数据源失败: {str(e)}', 'danger')
        return render_template('crawler/index.html')

@crawler_bp.route('/add_source', methods=['GET', 'POST'])
@login_required
def add_source():
    """添加数据源"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            name = request.form['name']
            type = request.form['type']
            url = request.form['url']
            config = request.form.get('config', '{}')
            
            # 验证
            if not name or not type:
                flash('请填写名称和类型', 'danger')
                return redirect(url_for('crawler.add_source'))
            
            # 解析配置
            try:
                config_json = json.loads(config)
            except json.JSONDecodeError:
                flash('配置格式错误，必须是JSON格式', 'danger')
                return redirect(url_for('crawler.add_source'))
            
            # 创建数据源
            new_source = DataSource(
                name=name,
                type=type,
                url=url if url else None,
                config=json.dumps(config_json)
            )
            
            db.session.add(new_source)
            db.session.commit()
            
            flash('数据源添加成功', 'success')
            return redirect(url_for('crawler.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'添加数据源失败: {str(e)}', 'danger')
            return redirect(url_for('crawler.add_source'))
    
    return render_template('crawler/add_source.html')

@crawler_bp.route('/edit_source/<int:source_id>', methods=['GET', 'POST'])
@login_required
def edit_source(source_id):
    """编辑数据源"""
    source = DataSource.query.get_or_404(source_id)
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            source.name = request.form['name']
            source.type = request.form['type']
            source.url = request.form['url']
            config = request.form.get('config', '{}')
            
            # 解析配置
            try:
                config_json = json.loads(config)
                source.config = json.dumps(config_json)
            except json.JSONDecodeError:
                flash('配置格式错误，必须是JSON格式', 'danger')
                return redirect(url_for('crawler.edit_source', source_id=source_id))
            
            db.session.commit()
            flash('数据源更新成功', 'success')
            return redirect(url_for('crawler.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新数据源失败: {str(e)}', 'danger')
            return redirect(url_for('crawler.edit_source', source_id=source_id))
    
    # 准备编辑数据
    source.config = json.loads(source.config)
    return render_template('crawler/edit_source.html', source=source)

@crawler_bp.route('/delete_source/<int:source_id>')
@login_required
def delete_source(source_id):
    """删除数据源"""
    try:
        source = DataSource.query.get_or_404(source_id)
        db.session.delete(source)
        db.session.commit()
        flash('数据源删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除数据源失败: {str(e)}', 'danger')
    
    return redirect(url_for('crawler.index'))

@crawler_bp.route('/crawl/<int:source_id>')
@login_required
def crawl(source_id):
    """爬取指定数据源"""
    try:
        source = DataSource.query.get_or_404(source_id)
        config = json.loads(source.config)
        
        # 根据数据源类型调用不同的爬取方法
        if source.type == 'web':
            results = crawl_web(source, config)
        elif source.type == 'api':
            results = crawl_api(source, config)
        elif source.type == 'file':
            results = crawl_file(source, config)
        else:
            flash(f'不支持的数据源类型: {source.type}', 'danger')
            return redirect(url_for('crawler.index'))
        
        # 保存爬取结果
        save_crawled_data(source, results)
        
        flash(f'爬取完成，共获取 {len(results)} 条数据', 'success')
        return redirect(url_for('crawler.view_data', source_id=source_id))
        
    except Exception as e:
        flash(f'爬取失败: {str(e)}', 'danger')
        return redirect(url_for('crawler.index'))

@crawler_bp.route('/view_data/<int:source_id>')
@login_required
def view_data(source_id):
    """查看爬取的数据"""
    try:
        source = DataSource.query.get_or_404(source_id)
        crawled_data = CrawledData.query.filter_by(source_id=source_id)\
                                        .order_by(CrawledData.crawled_at.desc())\
                                        .all()
        
        return render_template('crawler/view_data.html', source=source, crawled_data=crawled_data)
        
    except Exception as e:
        flash(f'获取爬取数据失败: {str(e)}', 'danger')
        return redirect(url_for('crawler.index'))

# 爬取方法实现
def crawl_web(source, config):
    """爬取网页数据"""
    results = []
    
    try:
        # 发送请求
        response = requests.get(source.url, timeout=Config.API_TIMEOUT)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 根据配置提取数据
        elements = soup.select(config.get('selector', 'body'))
        
        for i, element in enumerate(elements):
            title = element.select_one(config.get('title_selector', 'h1,h2,h3')).text.strip() if element.select_one(config.get('title_selector', 'h1,h2,h3')) else f'标题 {i+1}'
            content = element.select_one(config.get('content_selector', '*')).text.strip() if element.select_one(config.get('content_selector', '*')) else element.text.strip()
            
            results.append({
                'title': title,
                'content': content,
                'url': source.url,
                'metadata': {
                    'source_type': 'web',
                    'selector': config.get('selector'),
                    'crawled_at': datetime.utcnow().isoformat()
                }
            })
            
    except Exception as e:
        raise Exception(f'网页爬取失败: {str(e)}')
    
    return results

def crawl_api(source, config):
    """爬取API数据"""
    results = []
    
    try:
        # 构建请求参数
        method = config.get('method', 'GET')
        headers = config.get('headers', {})
        params = config.get('params', {})
        data = config.get('data', {})
        
        # 发送请求
        if method.upper() == 'POST':
            response = requests.post(source.url, headers=headers, params=params, json=data, timeout=Config.API_TIMEOUT)
        else:
            response = requests.get(source.url, headers=headers, params=params, timeout=Config.API_TIMEOUT)
        
        response.raise_for_status()
        api_data = response.json()
        
        # 提取数据
        items = api_data
        if 'items_key' in config:
            # 根据配置的键路径提取数据
            for key in config['items_key'].split('.'):
                items = items[key]
        
        # 处理数据项
        for item in items:
            # 根据配置提取标题和内容
            title = extract_from_dict(item, config.get('title_path', ''))
            content = extract_from_dict(item, config.get('content_path', ''))
            
            results.append({
                'title': title or '未命名',
                'content': content or str(item),
                'url': source.url,
                'metadata': {
                    'source_type': 'api',
                    'method': method,
                    'response_status': response.status_code,
                    'crawled_at': datetime.utcnow().isoformat()
                }
            })
            
    except Exception as e:
        raise Exception(f'API爬取失败: {str(e)}')
    
    return results

def crawl_file(source, config):
    """爬取文件数据"""
    results = []
    
    try:
        file_path = config.get('file_path', source.url)
        file_type = config.get('file_type', 'csv')
        
        if not os.path.exists(file_path):
            raise Exception(f'文件不存在: {file_path}')
        
        if file_type == 'csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 根据配置提取标题和内容
                    title = extract_from_dict(row, config.get('title_column', ''))
                    content = extract_from_dict(row, config.get('content_column', ''))
                    
                    results.append({
                        'title': title or '未命名',
                        'content': content or str(row),
                        'url': source.url,
                        'metadata': {
                            'source_type': 'file',
                            'file_path': file_path,
                            'file_type': file_type,
                            'crawled_at': datetime.utcnow().isoformat()
                        }
                    })
        elif file_type == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 如果是列表，直接处理；如果是字典，提取items
                items = data if isinstance(data, list) else data.get('items', [])
                
                for item in items:
                    title = extract_from_dict(item, config.get('title_path', ''))
                    content = extract_from_dict(item, config.get('content_path', ''))
                    
                    results.append({
                        'title': title or '未命名',
                        'content': content or str(item),
                        'url': source.url,
                        'metadata': {
                            'source_type': 'file',
                            'file_path': file_path,
                            'file_type': file_type,
                            'crawled_at': datetime.utcnow().isoformat()
                        }
                    })
        else:
            raise Exception(f'不支持的文件类型: {file_type}')
            
    except Exception as e:
        raise Exception(f'文件爬取失败: {str(e)}')
    
    return results

def save_crawled_data(source, results):
    """保存爬取的数据到数据库"""
    try:
        for result in results:
            crawled_data = CrawledData(
                source_id=source.id,
                title=result['title'],
                content=result['content'],
                url=result['url'],
                metadata=json.dumps(result['metadata'])
            )
            db.session.add(crawled_data)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f'保存爬取数据失败: {str(e)}')

def extract_from_dict(data, path):
    """从字典中根据路径提取数据"""
    if not path or not data:
        return None
    
    keys = path.split('.')
    value = data
    
    try:
        for key in keys:
            if isinstance(value, list):
                value = value[int(key)]
            else:
                value = value[key]
        return value
    except (KeyError, IndexError, TypeError):
        return None