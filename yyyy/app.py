import json
import os
import re
import asyncio
import math
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

# 智能对话回复生成函数
def generate_ai_response(user_query):
    # 转换为小写以便匹配
    query = user_query.lower()
    
    # 1. 问候语
    greetings = ['你好', 'hi', 'hello', '早上好', '下午好', '晚上好', '晚安', '早', '嗨']
    for greeting in greetings:
        if greeting in query:
            return f"{greeting}！我是川小农AI助手，有什么可以帮助你的吗？"
    
    # 2. 询问名字
    if '叫什么' in query or '名字' in query or '是谁' in query:
        return "我是川小农AI助手，很高兴为你服务！"
    
    # 3. 时间查询
    if '时间' in query or '几点' in query:
        now = datetime.now()
        return f"当前时间是：{now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 4. 日期查询
    if '日期' in query or '今天' in query and ('几号' in query or '日期' in query):
        now = datetime.now()
        return f"今天是：{now.strftime('%Y年%m月%d日')}"
    
    # 5. 数学计算
    math_patterns = [
        (r'(\d+)\s*\+\s*(\d+)', lambda x, y: int(x) + int(y)),
        (r'(\d+)\s*-\s*(\d+)', lambda x, y: int(x) - int(y)),
        (r'(\d+)\s*\*\s*(\d+)', lambda x, y: int(x) * int(y)),
        (r'(\d+)\s*/\s*(\d+)', lambda x, y: int(x) / int(y) if int(y) != 0 else "除数不能为零！"),
        (r'(\d+)的平方', lambda x: int(x) ** 2),
        (r'(\d+)的平方根', lambda x: math.sqrt(int(x)) if int(x) >= 0 else "负数没有实数平方根！")
    ]
    
    for pattern, func in math_patterns:
        match = re.search(pattern, query)
        if match:
            if len(match.groups()) == 2:
                result = func(match.group(1), match.group(2))
            else:
                result = func(match.group(1))
            return f"计算结果：{result}"
    
    # 6. 电影功能帮助
    if '电影' in query and ('怎么' in query or '如何' in query or '使用' in query):
        return "使用@电影命令可以播放视频，格式：@电影 视频URL。支持YouTube、Vimeo和直接视频文件。"
    
    # 7. 帮助信息
    if '帮助' in query or '功能' in query or '怎么用' in query:
        return "我可以帮助你：\n1. 聊天对话\n2. 查询时间日期\n3. 简单数学计算\n4. 播放电影（@电影 URL）\n5. 查看在线用户"
    
    # 8. 在线用户查询
    if '在线' in query and ('人' in query or '用户' in query):
        user_count = len(online_users)
        if user_count == 0:
            return "当前没有其他在线用户。"
        elif user_count == 1:
            return "当前有1位在线用户。"
        else:
            return f"当前有{user_count}位在线用户。"
    
    # 9. 退出相关
    if '退出' in query or '离开' in query:
        return "点击右上角的退出按钮可以离开聊天室。"
    
    # 10. 感谢类
    if '谢谢' in query or '感谢' in query or 'thank' in query:
        return "不客气，很高兴能帮到你！"
    
    # 11. 闲聊回复
    casual_responses = [
        "这个问题很有意思！",
        "让我想想...",
        "你能告诉我更多吗？",
        "我理解你的意思。",
        "这是个好问题！",
        "我也觉得是这样。",
        "很有见解！"
    ]
    
    # 12. 默认回复
    default_responses = [
        "抱歉，我不太理解你的意思。",
        "能换个方式问吗？",
        "我正在学习中，还不太明白这个问题。",
        "你可以试试问我其他问题。"
    ]
    
    # 简单的随机回复选择（伪随机，根据查询长度选择）
    if len(query) < 5:
        return casual_responses[len(query) % len(casual_responses)]
    else:
        return default_responses[len(query) % len(default_responses)]


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储在线用户信息
online_users = {}
# 存储聊天记录
chat_history = []
MAX_HISTORY = 100

# 加载配置
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/config')
def get_config():
    return jsonify(config)

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    if username in online_users:
        return jsonify({'exists': True})
    return jsonify({'exists': False})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    for username, user_data in list(online_users.items()):
        if user_data['sid'] == sid:
            del online_users[username]
            # 广播用户离开消息
            socketio.emit('user_left', {'username': username, 'users': list(online_users.keys())})
            leave_room('chatroom')
            print(f'{username} disconnected')
            break

@socketio.on('join')
def handle_join(data):
    username = data['username']
    if username in online_users:
        emit('join_error', {'message': '用户名已存在'})
        return
    
    online_users[username] = {'sid': request.sid, 'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    join_room('chatroom')
    
    # 发送历史消息给新用户
    emit('history', {'messages': chat_history})
    
    # 广播新用户加入消息
    socketio.emit('user_joined', {'username': username, 'users': list(online_users.keys())}, room='chatroom')
    print(f'{username} joined')

@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    message = data['message']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 检查@命令
    processed_message = message
    message_type = 'text'
    command_data = None
    
    # 检查@电影命令
    movie_match = re.search(r'@电影\s+(.+)', message)
    if movie_match:
        message_type = 'movie'
        movie_url = movie_match.group(1).strip()
        # 预处理视频URL，确保兼容性
        # 处理YouTube短链接
        if movie_url.startswith('https://youtu.be/'):
            movie_url = movie_url.replace('https://youtu.be/', 'https://www.youtube.com/watch?v=')
        # 处理没有协议的URL
        elif not movie_url.startswith('http://') and not movie_url.startswith('https://'):
            movie_url = 'https://' + movie_url
        command_data = {'url': movie_url}
    
    # 检查@川小农命令
    elif message.startswith('@川小农'):
        message_type = 'ai_query'
        user_query = message[4:].strip()
        command_data = {'query': user_query}
        
        # 智能对话处理 - 根据用户输入提供不同回复
        ai_response = generate_ai_response(user_query)
        
        ai_message = {
            'type': 'ai_response',
            'username': '川小农',
            'content': ai_response,
            'timestamp': timestamp
        }
        chat_history.append(ai_message)
        if len(chat_history) > MAX_HISTORY:
            chat_history.pop(0)
        socketio.emit('new_message', ai_message, room='chatroom')
    
    # 处理@用户名提醒
    mentions = re.findall(r'@(\S+)', message)
    mentioned_users = []
    for mention in mentions:
        if mention in online_users and mention != '电影' and mention != '川小农':
            mentioned_users.append(mention)
    
    # 构造消息对象
    chat_message = {
        'type': message_type,
        'username': username,
        'content': processed_message,
        'timestamp': timestamp,
        'mentions': mentioned_users,
        'command_data': command_data
    }
    
    # 保存到历史记录
    chat_history.append(chat_message)
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)
    
    # 广播消息
    socketio.emit('new_message', chat_message, room='chatroom')
    
    # 发送特殊提醒给被@的用户
    for mentioned_user in mentioned_users:
        socketio.emit('mention_alert', {
            'from_user': username,
            'message': message
        }, to=online_users[mentioned_user]['sid'])

@socketio.on('typing')
def handle_typing(data):
    username = data['username']
    socketio.emit('user_typing', {'username': username}, room='chatroom', skip_sid=request.sid)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    username = data['username']
    socketio.emit('user_stopped_typing', {'username': username}, room='chatroom', skip_sid=request.sid)

if __name__ == '__main__':
    # 确保templates目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)