"""
数据库模块
处理房间信息和密码存储
"""
import sqlite3
import hashlib
import os
from datetime import datetime

DATABASE_FILE = 'collab.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()

    # 创建房间表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            password_hash TEXT,
            created_at TEXT,
            content TEXT DEFAULT ''
        )
    ''')

    # 创建用户会话表（用于密码记忆）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            room_id TEXT,
            password TEXT,
            created_at TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms (room_id)
        )
    ''')

    # 创建文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            room_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_at TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms (room_id)
        )
    ''')

    # 检查是否需要为现有files表添加room_id列
    cursor.execute("PRAGMA table_info(files)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'room_id' not in columns:
        print("添加room_id列到files表...")
        cursor.execute("ALTER TABLE files ADD COLUMN room_id TEXT")
        cursor.execute("UPDATE files SET room_id = 'default' WHERE room_id IS NULL")
        conn.commit()

    # 创建默认public房间（如果不存在）
    cursor.execute('SELECT room_id FROM rooms WHERE room_id = ?', ('public',))
    if not cursor.fetchone():
        print("创建默认public房间...")
        cursor.execute('''
            INSERT OR IGNORE INTO rooms (room_id, password_hash, created_at, content)
            VALUES (?, ?, ?, ?)
        ''', ('public', None, datetime.now().isoformat(), ''))

    conn.commit()
    conn.close()

def create_room(room_id, password=None):
    """创建房间"""
    conn = get_db()
    cursor = conn.cursor()

    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute('''
            INSERT INTO rooms (room_id, password_hash, created_at, content)
            VALUES (?, ?, ?, ?)
        ''', (room_id, password_hash, datetime.now().isoformat(), ''))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # 房间已存在
        conn.close()
        return False

def verify_room_password(room_id, password):
    """验证房间密码"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT password_hash FROM rooms WHERE room_id = ?', (room_id,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return False

    if result['password_hash'] is None:
        # 公开房间，无需密码
        return True

    if password is None or password == '':
        # 私密房间但未提供密码
        return False

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return result['password_hash'] == password_hash

def get_room(room_id):
    """获取房间信息"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM rooms WHERE room_id = ?', (room_id,))
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None

def save_room_content(room_id, content):
    """保存房间内容"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('UPDATE rooms SET content = ? WHERE room_id = ?', (content, room_id))
    conn.commit()
    conn.close()

def get_room_content(room_id):
    """获取房间内容"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT content FROM rooms WHERE room_id = ?', (room_id,))
    result = cursor.fetchone()
    conn.close()

    return result['content'] if result else ''

def set_session_password(session_id, room_id, password):
    """保存用户密码会话"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO user_sessions (session_id, room_id, password, created_at)
        VALUES (?, ?, ?, ?)
    ''', (session_id, room_id, password, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_session_password(session_id, room_id):
    """获取用户密码会话"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT password FROM user_sessions
        WHERE session_id = ? AND room_id = ?
    ''', (session_id, room_id))
    result = cursor.fetchone()
    conn.close()

    return result['password'] if result else None

def delete_session(session_id):
    """删除用户会话"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM user_sessions WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

def reset_room_password(room_id, old_password, new_password):
    """重置房间密码"""
    conn = get_db()
    cursor = conn.cursor()

    # 验证旧密码
    if not verify_room_password(room_id, old_password):
        conn.close()
        return False

    # 设置新密码
    new_password_hash = None
    if new_password:
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()

    cursor.execute('UPDATE rooms SET password_hash = ? WHERE room_id = ?', (new_password_hash, room_id))
    conn.commit()
    conn.close()

    # 清除所有保存的密码会话
    delete_all_room_sessions(room_id)

    return True

def delete_all_room_sessions(room_id):
    """删除房间的所有会话"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM user_sessions WHERE room_id = ?', (room_id,))
    conn.commit()
    conn.close()

def get_all_rooms():
    """获取所有房间信息（管理员功能）"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT room_id, password_hash, created_at FROM rooms ORDER BY created_at DESC')
    results = cursor.fetchall()
    conn.close()

    rooms = []
    for row in results:
        rooms.append({
            'room_id': row['room_id'],
            'is_public': row['password_hash'] is None,
            'created_at': row['created_at']
        })

    return rooms

def delete_room(room_id):
    """删除房间"""
    # 不能删除默认public房间
    if room_id == 'public':
        return False

    conn = get_db()
    cursor = conn.cursor()

    # 检查房间是否存在
    cursor.execute('SELECT room_id FROM rooms WHERE room_id = ?', (room_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return False

    # 删除房间相关的会话
    cursor.execute('DELETE FROM user_sessions WHERE room_id = ?', (room_id,))

    # 删除房间的文件
    cursor.execute('SELECT filename FROM files WHERE room_id = ?', (room_id,))
    files = cursor.fetchall()

    for file_row in files:
        file_path = os.path.join('..', 'files', file_row['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

    cursor.execute('DELETE FROM files WHERE room_id = ?', (room_id,))

    # 删除房间
    cursor.execute('DELETE FROM rooms WHERE room_id = ?', (room_id,))

    conn.commit()
    conn.close()
    return True

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    print("数据库初始化完成")

# ==================== 文件管理功能 ====================

def add_file(file_id, room_id, filename, original_filename, file_size, description=''):
    """添加文件记录"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO files (file_id, room_id, filename, original_filename, file_size, uploaded_at, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (file_id, room_id, filename, original_filename, file_size, datetime.now().isoformat(), description))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_all_files(room_id=None):
    """获取所有文件列表，可按房间过滤"""
    conn = get_db()
    cursor = conn.cursor()

    if room_id:
        cursor.execute('SELECT * FROM files WHERE room_id = ? ORDER BY uploaded_at DESC', (room_id,))
    else:
        cursor.execute('SELECT * FROM files ORDER BY uploaded_at DESC')
    results = cursor.fetchall()
    conn.close()

    files = []
    for row in results:
        files.append({
            'file_id': row['file_id'],
            'room_id': row['room_id'],
            'filename': row['filename'],
            'original_filename': row['original_filename'],
            'file_size': row['file_size'],
            'uploaded_at': row['uploaded_at'],
            'description': row['description']
        })

    return files

def get_file(file_id):
    """获取文件信息"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM files WHERE file_id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None

def delete_file(file_id):
    """删除文件记录"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT file_id FROM files WHERE file_id = ?', (file_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return False

    cursor.execute('DELETE FROM files WHERE file_id = ?', (file_id,))
    conn.commit()
    conn.close()
    return True

def delete_room_files(room_id):
    """删除房间的所有文件"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT filename FROM files WHERE room_id = ?', (room_id,))
    files = cursor.fetchall()

    for file_row in files:
        file_path = os.path.join('..', 'files', file_row['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

    cursor.execute('DELETE FROM files WHERE room_id = ?', (room_id,))
    conn.commit()
    conn.close()
