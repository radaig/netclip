@echo off
REM Netclip 快速启动脚本 (Windows)

echo 🚀 启动 Netclip 协作编辑平台...
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查是否已安装依赖
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

echo 📚 安装依赖包...
pip install -q -r requirements.txt

echo.
echo ✅ 环境准备完成！
echo.
echo 🌐 启动服务器在 http://localhost:8080
echo 🔑 管理后台: http://localhost:8080/admin ^(密码: admin123^)
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动服务器
python server.py

pause
