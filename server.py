from flask import Flask, request, jsonify, send_from_directory, send_file, make_response, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
import uuid
from datetime import datetime
import os
import db

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 获取当前目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 初始化数据库
db.init_db()

# 文件类型安全配置
ALLOWED_EXTENSIONS = {
    # 图片
    'jpg': {'mime': 'image/jpeg', 'max_size': 10 * 1024 * 1024, 'headers': [b'\xff\xd8\xff']},
    'jpeg': {'mime': 'image/jpeg', 'max_size': 10 * 1024 * 1024, 'headers': [b'\xff\xd8\xff']},
    'png': {'mime': 'image/png', 'max_size': 10 * 1024 * 1024, 'headers': [b'\x89PNG\r\n\x1a\n']},
    'gif': {'mime': 'image/gif', 'max_size': 10 * 1024 * 1024, 'headers': [b'GIF87a', b'GIF89a']},
    'webp': {'mime': 'image/webp', 'max_size': 10 * 1024 * 1024, 'headers': [b'RIFF', b'WEBP']},
    'svg': {'mime': 'image/svg+xml', 'max_size': 5 * 1024 * 1024, 'headers': [b'<?xml']},
    # 文档
    'txt': {'mime': 'text/plain', 'max_size': 5 * 1024 * 1024, 'headers': None},
    'md': {'mime': 'text/markdown', 'max_size': 5 * 1024 * 1024, 'headers': None},
    'pdf': {'mime': 'application/pdf', 'max_size': 100 * 1024 * 1024, 'headers': [b'%PDF']},
    'doc': {'mime': 'application/msword', 'max_size': 100 * 1024 * 1024, 'headers': [b'\xd0\xcf\x11\xe0']},
    'docx': {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'max_size': 100 * 1024 * 1024, 'headers': [b'PK']},
    'xls': {'mime': 'application/vnd.ms-excel', 'max_size': 100 * 1024 * 1024, 'headers': [b'\xd0\xcf\x11\xe0']},
    'xlsx': {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'max_size': 100 * 1024 * 1024, 'headers': [b'PK']},
    'ppt': {'mime': 'application/vnd.ms-powerpoint', 'max_size': 100 * 1024 * 1024, 'headers': [b'\xd0\xcf\x11\xe0']},
    'pptx': {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'max_size': 100 * 1024 * 1024, 'headers': [b'PK']},
    # 压缩文件
    'zip': {'mime': 'application/zip', 'max_size': 100 * 1024 * 1024, 'headers': [b'PK']},
    'rar': {'mime': 'application/x-rar-compressed', 'max_size': 100 * 1024 * 1024, 'headers': [b'Rar!']},
    '7z': {'mime': 'application/x-7z-compressed', 'max_size': 100 * 1024 * 1024, 'headers': [b'7z\xbc\xaf\x27\x1c']},
    # 代码文件
    'js': {'mime': 'text/javascript', 'max_size': 5 * 1024 * 1024, 'headers': None},
    'json': {'mime': 'application/json', 'max_size': 5 * 1024 * 1024, 'headers': None},
    'html': {'mime': 'text/html', 'max_size': 5 * 1024 * 1024, 'headers': [b'<!DOCTYPE', b'<html']},
    'htm': {'mime': 'text/html', 'max_size': 5 * 1024 * 1024, 'headers': [b'<!DOCTYPE', b'<html']},
    'css': {'mime': 'text/css', 'max_size': 5 * 1024 * 1024, 'headers': None},
    'xml': {'mime': 'text/xml', 'max_size': 5 * 1024 * 1024, 'headers': [b'<?xml', b'<']},
    'py': {'mime': 'text/x-python', 'max_size': 5 * 1024 * 1024, 'headers': None},
    'java': {'mime': 'text/x-java-source', 'max_size': 5 * 1024 * 1024, 'headers': None},
    # 音频文件
    'mp3': {'mime': 'audio/mpeg', 'max_size': 50 * 1024 * 1024, 'headers': [b'ID3', b'\xff\xfb', b'\xff\xfa']},
    'wav': {'mime': 'audio/wav', 'max_size': 50 * 1024 * 1024, 'headers': [b'RIFF', b'WAVE']},
    'ogg': {'mime': 'audio/ogg', 'max_size': 50 * 1024 * 1024, 'headers': [b'OggS']},
    # 视频文件
    'mp4': {'mime': 'video/mp4', 'max_size': 100 * 1024 * 1024, 'headers': [b'ftyp']},
    'avi': {'mime': 'video/x-msvideo', 'max_size': 100 * 1024 * 1024, 'headers': [b'RIFF', b'AVI ']},
    'mov': {'mime': 'video/quicktime', 'max_size': 100 * 1024 * 1024, 'headers': [b'ftyp']},
    'wmv': {'mime': 'video/x-ms-wmv', 'max_size': 100 * 1024 * 1024, 'headers': [b'RIFF', b'WMVF']}
}

def validate_file_security(filename, file_content, mime_type):
    """验证文件安全性"""
    # 获取文件扩展名
    if '.' not in filename:
        return False, "文件必须包含扩展名"

    file_extension = filename.split('.').pop().lower()

    # 检查扩展名是否允许
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件扩展名: {file_extension}"

    file_config = ALLOWED_EXTENSIONS[file_extension]

    # 验证MIME类型
    if mime_type and mime_type != file_config['mime']:
        return False, f"MIME类型不匹配: 期望 {file_config['mime']}, 实际 {mime_type}"

    # 检查文件头（Magic Number）
    if file_config['headers'] and len(file_content) > 0:
        file_header = file_content[:16]  # 读取前16字节
        is_valid_header = False
        for header in file_config['headers']:
            if file_header.startswith(header):
                is_valid_header = True
                break
        if not is_valid_header:
            return False, "文件头验证失败，文件可能已损坏或被篡改"

    # 检查文件名安全性
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '~', '$']
    for char in dangerous_chars:
        if char in filename:
            return False, f"文件名包含非法字符: {char}"

    # 检查文件名长度
    if len(filename) > 100:
        return False, "文件名长度不能超过100个字符"

    return True, "验证通过"

# 存储实时用户信息（不持久化）
users = {}  # {socket_id: {'username': str, 'room': str, 'session_id': str}}

# 配置图片保存路径
UPLOAD_FOLDER = 'images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """
    处理图片上传
    """
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        file = request.files['image']

        # 检查文件是否为空
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        # 获取文件扩展名
        file_extension = os.path.splitext(file.filename)[1]

        # 生成文件名：uuid + 时间戳 + 扩展名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        unique_filename = f"{uuid.uuid4()}_{timestamp}{file_extension}"

        # 保存文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # 返回图片URL
        image_url = f"/images/{unique_filename}"
        return jsonify({'url': image_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
def serve_image(filename):
    """
    提供图片访问服务
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    """
    重定向到默认public房间
    """
    return redirect('/public')

@app.route('/public')
def public_room():
    """
    提供默认public房间
    """
    try:
        with open(os.path.join(BASE_DIR, 'tuieditor.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "tuieditor.html not found", 404

@app.route('/<room_id>')
def room_page(room_id):
    """
    房间页面 - /room_id 形式访问
    """
    try:
        with open(os.path.join(BASE_DIR, 'tuieditor.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "tuieditor.html not found", 404

@app.route('/tuieditor.html')
def editor():
    """
    提供编辑器页面
    """
    try:
        with open(os.path.join(BASE_DIR, 'tuieditor.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "tuieditor.html not found", 404

@app.route('/admin')
def admin():
    """
    提供管理员页面
    """
    try:
        with open(os.path.join(BASE_DIR, 'admin.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "admin.html not found", 404

# ==================== WebSocket 协作功能 ====================

@socketio.on('join')
def handle_join(data):
    """用户加入房间"""
    room_id = data.get('room', 'default')
    username = data.get('username', '')
    session_id = data.get('session_id', '')

    # 验证密码
    password = data.get('password', None)

    # 从Cookie或会话中获取已保存的密码
    if not password and session_id:
        saved_password = db.get_session_password(session_id, room_id)
        if saved_password:
            password = saved_password

    if not db.verify_room_password(room_id, password):
        emit('auth_failed', {'message': '密码错误'})
        return

    # 记录用户信息
    users[request.sid] = {'username': username, 'room': room_id, 'session_id': session_id}

    # 加入房间
    join_room(room_id)

    # 获取房间当前内容（从数据库）
    room_content = db.get_room_content(room_id)

    # 向新用户发送当前内容
    emit('init_content', {'content': room_content})

    # 获取当前房间所有用户列表（包括自己）
    user_list = [u['username'] for u in users.values() if u['room'] == room_id]

    # 向新用户发送当前用户列表
    emit('user_list_update', {'users': user_list})

    # 通知房间内其他用户有新用户加入
    emit('user_joined', {
        'username': username,
        'users': user_list
    }, to=room_id, include_self=False)

    print(f"[WebSocket] 用户 {username} 加入房间 {room_id}, 当前在线人数: {len(user_list)}")

@socketio.on('leave')
def handle_leave(data):
    """用户离开房间"""
    if request.sid in users:
        user = users[request.sid]
        room_id = user['room']
        username = user['username']

        # 离开房间
        leave_room(room_id)

        # 移除用户信息
        del users[request.sid]

        # 通知房间内其他用户
        user_list = [u['username'] for u in users.values() if u['room'] == room_id]
        emit('user_left', {
            'username': username,
            'users': user_list
        }, to=room_id)

        print(f"[WebSocket] 用户 {username} 离开房间 {room_id}")

@socketio.on('content_change')
def handle_content_change(data):
    """处理内容变更"""
    room_id = data.get('room', 'default')
    content = data.get('content', '')
    username = users.get(request.sid, {}).get('username', 'Unknown')

    # 保存房间内容到数据库
    db.save_room_content(room_id, content)

    # 广播给房间内其他用户
    emit('content_update', {
        'content': content,
        'username': username,
        'timestamp': datetime.now().isoformat()
    }, to=room_id, include_self=False)

    print(f"[WebSocket] 房间 {room_id} - {username} 更新内容 (长度: {len(content)})")

@socketio.on('cursor_move')
def handle_cursor_move(data):
    """处理光标位置同步"""
    room_id = data.get('room', 'default')
    cursor_position = data.get('position', 0)
    username = users.get(request.sid, {}).get('username', 'Unknown')

    # 广播光标位置给其他用户
    emit('cursor_update', {
        'username': username,
        'position': cursor_position
    }, to=room_id, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """用户断开连接"""
    if request.sid in users:
        user = users[request.sid]
        room_id = user['room']
        username = user['username']

        # 移除用户信息
        del users[request.sid]

        # 通知房间内其他用户
        user_list = [u['username'] for u in users.values() if u['room'] == room_id]
        emit('user_left', {
            'username': username,
            'users': user_list
        }, to=room_id)

        print(f"[WebSocket] 用户 {username} 断开连接")

# 房间管理API
@app.route('/api/room/create', methods=['POST'])
def create_room():
    """创建新房间"""
    data = request.get_json() or {}
    password = data.get('password')
    custom_room_id = data.get('room_id')

    # 如果提供了自定义room_id，使用它；否则生成8位房间ID
    if custom_room_id:
        room_id = custom_room_id
    else:
        # 生成8位房间ID
        room_id = str(uuid.uuid4())[:8]

    # 创建房间（数据库中）
    if db.create_room(room_id, password):
        return jsonify({
            'room_id': room_id,
            'url': f'/{room_id}'
        }), 200
    else:
        error_msg = '房间创建失败'
        # 检查是否是room_id已存在
        if db.get_room(room_id):
            error_msg = f'房间ID "{room_id}" 已存在，请使用其他ID'
        return jsonify({'error': error_msg}), 500

@app.route('/api/room/verify', methods=['POST'])
def verify_room():
    """验证房间密码"""
    data = request.get_json() or {}
    room_id = data.get('room_id')
    password = data.get('password')
    session_id = data.get('session_id')

    if not room_id:
        return jsonify({'error': '缺少房间ID'}), 400

    # 首先检查房间是否存在
    room_info = db.get_room(room_id)
    if not room_info:
        return jsonify({
            'verified': False,
            'exists': False,
            'message': '房间不存在'
        }), 200

    # 房间存在，验证密码
    if db.verify_room_password(room_id, password):
        # 保存密码到会话
        if session_id:
            db.set_session_password(session_id, room_id, password)

        is_public = room_info['password_hash'] is None

        return jsonify({
            'verified': True,
            'exists': True,
            'room_id': room_id,
            'is_public': is_public
        }), 200
    else:
        return jsonify({
            'verified': False,
            'exists': True,
            'message': '密码错误'
        }), 401

@app.route('/api/room/<room_id>/users', methods=['GET'])
def get_room_users(room_id):
    """获取房间内用户列表"""
    user_list = [u['username'] for u in users.values() if u['room'] == room_id]
    return jsonify({'users': user_list}), 200

@app.route('/api/room/reset-password', methods=['POST'])
def reset_password():
    """重置房间密码"""
    data = request.get_json() or {}
    room_id = data.get('room_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not room_id:
        return jsonify({'error': '缺少房间ID'}), 400

    # 重置密码
    if db.reset_room_password(room_id, old_password, new_password):
        return jsonify({
            'success': True,
            'message': '密码重置成功',
            'room_id': room_id
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': '旧密码错误或房间不存在'
        }), 401

# ==================== 管理员 API ====================

@app.route('/api/admin/rooms', methods=['GET'])
def admin_get_rooms():
    """获取所有房间（管理员功能）"""
    rooms = db.get_all_rooms()
    return jsonify({'rooms': rooms}), 200

@app.route('/api/admin/reset-password', methods=['POST'])
def admin_reset_password():
    """管理员重置房间密码（无需旧密码）"""
    data = request.get_json() or {}
    room_id = data.get('room_id')
    new_password = data.get('new_password')

    if not room_id:
        return jsonify({'error': '缺少房间ID'}), 400

    # 管理员重置密码（绕过旧密码验证）
    conn = db.get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT room_id FROM rooms WHERE room_id = ?', (room_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    # 设置新密码
    new_password_hash = None
    if new_password:
        import hashlib
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()

    cursor.execute('UPDATE rooms SET password_hash = ? WHERE room_id = ?', (new_password_hash, room_id))
    conn.commit()
    conn.close()

    # 清除所有保存的密码会话
    db.delete_all_room_sessions(room_id)

    return jsonify({
        'success': True,
        'message': '密码重置成功',
        'room_id': room_id
    }), 200

@app.route('/api/admin/delete-room', methods=['POST'])
def admin_delete_room():
    """删除房间（管理员功能）"""
    data = request.get_json() or {}
    room_id = data.get('room_id')

    if not room_id:
        return jsonify({'error': '缺少房间ID'}), 400

    # 删除房间
    if db.delete_room(room_id):
        return jsonify({
            'success': True,
            'message': '房间已删除',
            'room_id': room_id
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

# ==================== 文件共享 API ====================

@app.route('/api/room/<room_id>/content', methods=['GET'])
def get_room_content_api(room_id):
    """获取房间剪贴板内容"""
    content = db.get_room_content(room_id)
    return jsonify({'content': content}), 200

@app.route('/api/room/<room_id>/files', methods=['GET'])
def get_room_files(room_id):
    """获取房间文件列表"""
    files = db.get_all_files(room_id)
    return jsonify({'files': files}), 200

@app.route('/api/room/<room_id>/upload', methods=['POST'])
def upload_room_file(room_id):
    """上传文件到指定房间"""
    try:
        # 检查房间是否存在
        room_info = db.get_room(room_id)
        if not room_info:
            return jsonify({'error': '房间不存在'}), 404

        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400

        file = request.files['file']
        description = request.form.get('description', '')

        # 检查文件是否为空
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        # 获取文件原始名称和MIME类型
        original_filename = file.filename
        mime_type = file.content_type

        # 先读取文件内容进行安全验证
        file_content = file.stream.read()
        file.stream.seek(0)  # 重置文件指针

        # 验证文件安全性
        is_valid, error_msg = validate_file_security(original_filename, file_content, mime_type)
        if not is_valid:
            return jsonify({'error': f'文件验证失败: {error_msg}'}), 400

        # 检查文件大小
        file_size = len(file_content)
        file_extension = original_filename.split('.').pop().lower()
        if file_size > ALLOWED_EXTENSIONS[file_extension]['max_size']:
            return jsonify({'error': f'文件大小超出限制，最大允许 {ALLOWED_EXTENSIONS[file_extension]["max_size"] / 1024 / 1024:.0f}MB'}), 400

        # 获取文件扩展名
        file_extension = os.path.splitext(original_filename)[1]

        # 生成文件ID和唯一文件名
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{room_id}_{file_id}_{timestamp}{file_extension}"

        # 保存文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'files', unique_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 重新写入文件内容
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 保存文件记录到数据库
        if db.add_file(file_id, room_id, unique_filename, original_filename, file_size, description):
            return jsonify({
                'success': True,
                'file_id': file_id,
                'filename': original_filename,
                'file_size': file_size,
                'message': '文件上传成功'
            }), 200
        else:
            # 如果数据库保存失败，删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': '文件记录保存失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/room/<room_id>/download/<file_id>', methods=['GET'])
def download_room_file(room_id, file_id):
    """下载房间文件"""
    try:
        # 从数据库获取文件信息
        file_info = db.get_file(file_id)

        if not file_info:
            return jsonify({'error': '文件不存在'}), 404

        # 验证文件属于该房间
        if file_info['room_id'] != room_id:
            return jsonify({'error': '文件不属于该房间'}), 403

        # 构建文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'files', file_info['filename'])

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info['original_filename']
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/room/<room_id>/delete/<file_id>', methods=['DELETE'])
def delete_room_file(room_id, file_id):
    """删除房间文件"""
    try:
        # 从数据库获取文件信息
        file_info = db.get_file(file_id)

        if not file_info:
            return jsonify({'error': '文件不存在'}), 404

        # 验证文件属于该房间
        if file_info['room_id'] != room_id:
            return jsonify({'error': '文件不属于该房间'}), 403

        # 删除物理文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'files', file_info['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # 从数据库删除记录
        if db.delete_file(file_id):
            return jsonify({
                'success': True,
                'message': '文件删除成功'
            }), 200
        else:
            return jsonify({'error': '文件删除失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 管理员文件管理 API ====================

@app.route('/api/admin/files', methods=['GET'])
def admin_get_all_files():
    """获取所有文件列表（管理员功能）"""
    files = db.get_all_files()
    return jsonify({'files': files}), 200

@app.route('/api/admin/delete-file/<file_id>', methods=['DELETE'])
def admin_delete_file(file_id):
    """删除文件（管理员功能）"""
    try:
        # 从数据库获取文件信息
        file_info = db.get_file(file_id)

        if not file_info:
            return jsonify({'error': '文件不存在'}), 404

        # 删除物理文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'files', file_info['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # 从数据库删除记录
        if db.delete_file(file_id):
            return jsonify({
                'success': True,
                'message': '文件删除成功',
                'file_id': file_id
            }), 200
        else:
            return jsonify({'error': '文件删除失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/download-file/<file_id>', methods=['GET'])
def admin_download_file(file_id):
    """下载文件（管理员功能）"""
    try:
        # 从数据库获取文件信息
        file_info = db.get_file(file_id)

        if not file_info:
            return jsonify({'error': '文件不存在'}), 404

        # 构建文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'files', file_info['filename'])

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info['original_filename']
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 使用SocketIO运行应用
    socketio.run(app, debug=True, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
