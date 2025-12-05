from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required
import pandas as pd
import numpy as np
import json
import os
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from models import db, CrawledData, AnalysisResult
from config import Config

# 创建分析器蓝图
analyzer_bp = Blueprint('analyzer', __name__, template_folder='templates')

@analyzer_bp.route('/')
@login_required
def index():
    """分析器主页"""
    try:
        # 获取最近的分析结果
        recent_results = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).limit(10).all()
        
        return render_template('analyzer/index.html', recent_results=recent_results)
        
    except Exception as e:
        flash(f'获取分析器数据失败: {str(e)}', 'danger')
        return render_template('analyzer/index.html')

@analyzer_bp.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    """数据分析页面"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            source_id = request.form.get('source_id')
            analysis_type = request.form['analysis_type']
            name = request.form['name']
            params = request.form.get('params', '{}')
            
            # 验证
            if not name or not analysis_type:
                flash('请填写名称和分析类型', 'danger')
                return redirect(url_for('analyzer.analyze'))
            
            # 解析参数
            try:
                params_json = json.loads(params)
            except json.JSONDecodeError:
                flash('参数格式错误，必须是JSON格式', 'danger')
                return redirect(url_for('analyzer.analyze'))
            
            # 获取数据
            if source_id:
                data = CrawledData.query.filter_by(source_id=source_id).all()
            else:
                data = CrawledData.query.all()
            
            if not data:
                flash('没有找到要分析的数据', 'danger')
                return redirect(url_for('analyzer.analyze'))
            
            # 将数据转换为DataFrame
            df = pd.DataFrame([{
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'url': item.url,
                'metadata': json.loads(item.metadata) if item.metadata else {},
                'crawled_at': item.crawled_at
            } for item in data])
            
            # 根据分析类型执行不同的分析
            if analysis_type == 'basic_stats':
                result = basic_statistics(df, params_json)
            elif analysis_type == 'text_analysis':
                result = text_analysis(df, params_json)
            elif analysis_type == 'sentiment_analysis':
                result = sentiment_analysis(df, params_json)
            elif analysis_type == 'machine_learning':
                result = machine_learning_analysis(df, params_json)
            elif analysis_type == 'correlation':
                result = correlation_analysis(df, params_json)
            else:
                flash(f'不支持的分析类型: {analysis_type}', 'danger')
                return redirect(url_for('analyzer.analyze'))
            
            # 保存分析结果
            save_analysis_result(name, analysis_type, result)
            
            flash('数据分析完成', 'success')
            return redirect(url_for('analyzer.results'))
            
        except Exception as e:
            flash(f'分析失败: {str(e)}', 'danger')
            return redirect(url_for('analyzer.analyze'))
    
    # GET请求，显示表单
    try:
        # 获取所有数据源
        from models import DataSource
        data_sources = DataSource.query.all()
        
        return render_template('analyzer/analyze.html', data_sources=data_sources)
        
    except Exception as e:
        flash(f'获取数据源失败: {str(e)}', 'danger')
        return render_template('analyzer/analyze.html')

@analyzer_bp.route('/results')
@login_required
def results():
    """分析结果页面"""
    try:
        # 获取所有分析结果
        analysis_results = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).all()
        
        return render_template('analyzer/results.html', analysis_results=analysis_results)
        
    except Exception as e:
        flash(f'获取分析结果失败: {str(e)}', 'danger')
        return render_template('analyzer/results.html')

@analyzer_bp.route('/result/<int:result_id>')
@login_required
def view_result(result_id):
    """查看分析结果详情"""
    try:
        result = AnalysisResult.query.get_or_404(result_id)
        result.content = json.loads(result.content)
        
        return render_template('analyzer/view_result.html', result=result)
        
    except Exception as e:
        flash(f'获取分析结果详情失败: {str(e)}', 'danger')
        return redirect(url_for('analyzer.results'))

@analyzer_bp.route('/delete_result/<int:result_id>')
@login_required
def delete_result(result_id):
    """删除分析结果"""
    try:
        result = AnalysisResult.query.get_or_404(result_id)
        db.session.delete(result)
        db.session.commit()
        flash('分析结果删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除分析结果失败: {str(e)}', 'danger')
    
    return redirect(url_for('analyzer.results'))

# 数据分析方法实现
def basic_statistics(df, params):
    """基础统计分析"""
    result = {
        'summary': df.describe(include='all').to_dict(),
        'total_records': len(df),
        'columns': list(df.columns),
        'null_values': df.isnull().sum().to_dict(),
        'data_types': df.dtypes.astype(str).to_dict()
    }
    
    return result

def text_analysis(df, params):
    """文本分析"""
    # 文本长度统计
    df['title_length'] = df['title'].str.len()
    df['content_length'] = df['content'].str.len()
    df['word_count'] = df['content'].str.split().str.len()
    
    # 最常见的词语
    text_column = params.get('text_column', 'content')
    n_words = params.get('n_words', 20)
    
    # 提取关键词
    vectorizer = CountVectorizer(stop_words='english' if params.get('language') == 'english' else None, max_features=n_words)
    X = vectorizer.fit_transform(df[text_column].fillna(''))
    word_counts = np.asarray(X.sum(axis=0)).ravel()
    word_list = vectorizer.get_feature_names_out()
    
    # 构建词频字典
    word_frequency = {word_list[i]: int(word_counts[i]) for i in range(len(word_list))}
    word_frequency = dict(sorted(word_frequency.items(), key=lambda x: x[1], reverse=True))
    
    result = {
        'text_statistics': {
            'title_length': df['title_length'].describe().to_dict(),
            'content_length': df['content_length'].describe().to_dict(),
            'word_count': df['word_count'].describe().to_dict()
        },
        'most_common_words': word_frequency,
        'total_unique_words': len(set(' '.join(df[text_column].fillna('')).split()))
    }
    
    return result

def sentiment_analysis(df, params):
    """情感分析（简单实现）"""
    # 简单的情感分析实现
    positive_words = params.get('positive_words', ['好', '优秀', '成功', '满意', '喜欢', 'good', 'great', 'success', 'excellent'])
    negative_words = params.get('negative_words', ['坏', '差', '失败', '不满意', '讨厌', 'bad', 'poor', 'failure', 'terrible'])
    
    def analyze_sentiment(text):
        if not text:
            return 0
        
        text_lower = text.lower()
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        return positive_score - negative_score
    
    # 分析标题和内容的情感
    df['title_sentiment'] = df['title'].apply(analyze_sentiment)
    df['content_sentiment'] = df['content'].apply(analyze_sentiment)
    
    # 计算情感分布
    sentiment_distribution = {
        'title_sentiment': df['title_sentiment'].value_counts().to_dict(),
        'content_sentiment': df['content_sentiment'].value_counts().to_dict()
    }
    
    result = {
        'sentiment_distribution': sentiment_distribution,
        'average_sentiment': {
            'title': float(df['title_sentiment'].mean()),
            'content': float(df['content_sentiment'].mean())
        },
        'sentiment_words': {
            'positive': positive_words,
            'negative': negative_words
        }
    }
    
    return result

def machine_learning_analysis(df, params):
    """机器学习分析"""
    # 简单的分类示例
    text_column = params.get('text_column', 'content')
    target_column = params.get('target_column')
    
    if not target_column:
        # 如果没有提供目标列，使用模拟的情感标签
        def get_sample_label(text):
            if len(text) > 500:
                return 1  # 长文本
            else:
                return 0  # 短文本
        
        df['sample_label'] = df[text_column].apply(get_sample_label)
        target_column = 'sample_label'
    
    # 准备数据
    X = df[text_column].fillna('')
    y = df[target_column]
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 特征提取
    vectorizer = CountVectorizer(max_features=1000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # 训练模型
    model = MultinomialNB()
    model.fit(X_train_vec, y_train)
    
    # 预测
    y_pred = model.predict(X_test_vec)
    
    # 评估
    report = classification_report(y_test, y_pred, output_dict=True)
    confusion = confusion_matrix(y_test, y_pred).tolist()
    
    # 保存模型
    model_filename = f'model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    model_path = os.path.join(Config.DATA_STORAGE_PATH, model_filename)
    
    with open(model_path, 'wb') as f:
        pickle.dump((model, vectorizer), f)
    
    result = {
        'model_info': {
            'type': 'Naive Bayes Classifier',
            'features': X_train_vec.shape[1],
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        },
        'classification_report': report,
        'confusion_matrix': confusion,
        'model_file': model_filename
    }
    
    return result

def correlation_analysis(df, params):
    """相关性分析"""
    # 只对数值列进行相关性分析
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_columns) < 2:
        return {
            'error': '需要至少两列数值数据来进行相关性分析'
        }
    
    # 计算相关系数
    correlation_matrix = df[numeric_columns].corr().to_dict()
    
    result = {
        'correlation_matrix': correlation_matrix,
        'numeric_columns': list(numeric_columns)
    }
    
    return result

def save_analysis_result(name, type, result):
    """保存分析结果"""
    try:
        analysis_result = AnalysisResult(
            name=name,
            type=type,
            content=json.dumps(result)
        )
        
        db.session.add(analysis_result)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f'保存分析结果失败: {str(e)}')

@analyzer_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """下载分析结果文件"""
    return send_from_directory(Config.DATA_STORAGE_PATH, filename, as_attachment=True)