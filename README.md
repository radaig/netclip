# Netclip - 实时协作编辑与文件共享平台

一个基于 Flask 和 Socket.IO 的实时协作编辑平台，支持多人同时编辑、文件共享和在线管理。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)
![Socket.IO](https://img.shields.io/badge/Socket.IO-5.0+-red)

在线编辑器引用 https://github.com/nhn/tui.editor 感谢🙏
## ✨ 功能特性

### 🎯 核心功能
- **实时多人协作编辑** - 基于 Toast UI Editor，支持 Markdown
- **房间管理** - 创建/加入房间，公开或私密房间（支持密码保护）
- **文件共享** - 安全上传、下载和管理文件
- **图片上传** - 支持点击上传和 Ctrl+V 粘贴图片
- **在线用户列表** - 实时显示协作者，动态更新
- **内容持久化** - SQLite 数据库保存所有内容

### 🔒 安全特性
- **双重文件验证** - 前端和后端双重验证文件类型
- **文件头检查** - 验证文件 Magic Number 防止伪造
- **MIME 类型验证** - 确保文件类型真实可靠
- **文件大小限制** - 根据文件类型动态限制大小
- **文件名安全** - 防止路径遍历和特殊字符攻击
- **密码保护** - 支持私密房间，智能密码记忆

### 🎛️ 管理功能
- **管理员后台** - 访问 `/admin` 进行管理
- **房间管理** - 重置密码、删除房间、查看内容
- **文件管理** - 查看、下载、删除所有文件
- **统计信息** - 实时显示房间和文件统计

## 📁 项目结构

```
.
├── server.py              # 主服务器（Flask + Socket.IO）
├── db.py                  # 数据库模块（SQLite3）
├── tuieditor.html         # 前端编辑器页面
├── admin.html             # 管理后台页面
├── requirements.txt       # Python 依赖
├── README.md              # 项目文档
├── static/                # 静态资源目录
├── images/                # 图片上传目录
├── files/                 # 文件共享目录
└── collab.db              # SQLite 数据库文件
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务器

```bash
python server.py
```

服务器将在 `http://localhost:8080` 启动

### 访问应用

- **协作编辑** - http://localhost:8080 或 http://localhost:8080/your-room-id
- **管理后台** - http://localhost:8080/admin (密码: admin123)

## 💡 使用说明

### 协作编辑

1. **访问编辑器**
   - 直接访问：http://localhost:8080 (进入默认公开房间)
   - 或访问：http://localhost:8080/room-id (进入特定房间)

2. **创建房间**
   - 在右侧面板输入房间ID和密码
   - 点击"创建/加入房间"按钮
   - 复制分享链接给协作者

3. **开始协作**
   - 所有用户打开同一个房间链接
   - 编辑内容会实时同步给所有用户
   - 右侧显示在线用户列表

### 文件上传

#### 支持的文件类型
- **图片**: JPG, PNG, GIF, WebP, SVG (最大 10MB)
- **文档**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, MD (最大 100MB)
- **代码**: JS, JSON, HTML, CSS, XML, PY, JAVA (最大 5MB)
- **压缩**: ZIP, RAR, 7Z (最大 100MB)
- **音视频**: MP3, WAV, OGG, MP4, AVI, MOV (最大 50-100MB)

#### 上传方式
1. **点击上传** - 点击"上传文件"按钮选择文件
2. **拖拽上传** - 直接拖拽文件到上传区域
3. **图片粘贴** - Ctrl+V 粘贴剪贴板图片（编辑器内）

### 管理后台

1. 访问：http://localhost:8080/admin
2. 输入管理员密码：`admin123`
3. 功能包括：
   - 查看所有房间统计
   - 重置房间密码
   - 删除房间
   - 查看和管理所有文件
   - 下载或删除文件

## 🔌 API 文档

### REST API

#### 创建房间
```http
POST /api/room/create
Content-Type: application/json

{
  "room_id": "custom-id",  # 可选，不提供则自动生成
  "password": "room-password"  # 可选，留空为公开房间
}
```

#### 验证房间
```http
POST /api/room/verify
Content-Type: application/json

{
  "room_id": "room-id",
  "password": "password",
  "session_id": "user-session-id"
}
```

#### 上传文件
```http
POST /api/room/{room_id}/upload
Content-Type: multipart/form-data

file: <binary>
description: "文件描述"  # 可选
```

#### 获取房间文件
```http
GET /api/room/{room_id}/files
```

#### 下载文件
```http
GET /api/room/{room_id}/download/{file_id}
```

#### 删除文件
```http
DELETE /api/room/{room_id}/delete/{file_id}
```

### WebSocket 事件

#### 客户端 → 服务器
- `join` - 加入房间
  ```javascript
  socket.emit('join', {
    room: 'room-id',
    username: '用户名',
    password: '房间密码',  // 私密房间需要
    session_id: '会话ID'
  })
  ```

- `content_change` - 内容变更
  ```javascript
  socket.emit('content_change', {
    room: 'room-id',
    content: 'markdown内容'
  })
  ```

- `cursor_move` - 光标位置
  ```javascript
  socket.emit('cursor_move', {
    room: 'room-id',
    position: 123
  })
  ```

#### 服务器 → 客户端
- `init_content` - 初始内容
- `content_update` - 内容更新
- `user_list_update` - 用户列表更新
- `user_joined` - 用户加入
- `user_left` - 用户离开
- `cursor_update` - 光标位置更新
- `auth_failed` - 认证失败

## 🛡️ 安全说明

### 文件上传安全
1. **前端验证** - 扩展名和 MIME 类型双重检查
2. **后端验证** - 文件头（Magic Number）验证
3. **大小限制** - 根据文件类型动态限制大小
4. **类型白名单** - 仅允许安全文件类型
5. **文件名过滤** - 防止路径遍历攻击

### 房间安全
1. **密码保护** - 私密房间需要密码
2. **会话管理** - 密码记忆功能（本地存储）
3. **会话隔离** - 每个房间独立管理
4. **管理员权限** - 管理员可重置密码

## 📦 依赖包

```
Flask==3.0.0
Flask-Cors==4.0.0
Flask-SocketIO==5.3.6
python-socketio==5.9.0
Werkzeug==3.0.1
```

## 🔧 配置

### 修改管理员密码

编辑 `admin.html`，修改常量：
```javascript
const ADMIN_PASSWORD = 'your-password';
```

### 修改端口

编辑 `server.py` 最后一行：
```python
socketio.run(app, debug=True, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
```

### 数据库位置

数据库文件：`collab.db`
- 房间信息：`rooms` 表
- 用户会话：`user_sessions` 表
- 文件记录：`files` 表

## 🐛 故障排除

### WebSocket 连接失败
- 检查防火墙设置
- 确认端口 8080 未被占用
- 查看浏览器控制台错误信息

### 文件上传失败
- 检查文件类型是否支持
- 确认文件大小未超限
- 查看服务器日志

### 协作同步问题
- 刷新页面重新连接
- 检查网络连接状态
- 查看控制台日志

## 📝 开发说明

### 技术栈
- **后端**: Python Flask + Socket.IO
- **数据库**: SQLite3
- **前端**: HTML5 + JavaScript + Toast UI Editor
- **实时通信**: WebSocket (Socket.IO)

### 主要模块
- `server.py` - 主服务器，处理 HTTP 请求和 WebSocket 事件
- `db.py` - 数据库操作模块
- `tuieditor.html` - 前端编辑器界面
- `admin.html` - 管理后台界面

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请在 GitHub 上创建 Issue。

---

⭐ 如果这个项目对你有帮助，请给个 Star！
