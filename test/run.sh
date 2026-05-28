#!/bin/bash
# 旅游收藏夹 演示项目 启动脚本

set -e

VENV_DIR="venv"
DATA_DB="data.db"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR"

echo "========================================"
echo "  旅游收藏夹 演示项目 (SQLite 版)"
echo "========================================"

# 创建虚拟环境
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "[1/5] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 安装 Python 依赖
echo "[2/5] 安装 Python 依赖..."
pip install fastapi uvicorn "python-jose[cryptography]" bcrypt pydantic -q

# 初始化数据库 + 导入数据
if [ ! -f "$DATA_DB" ]; then
    echo "[3/5] 导入数据（首次运行可能需要几分钟）..."
    python data/import_data.py
else
    echo "[3/5] 数据库已存在，跳过导入"
fi

# 安装前端依赖
if [ ! -d "node_modules" ]; then
    echo "[4/5] 安装前端依赖..."
    npm install
else
    echo "[4/5] 前端依赖已安装"
fi

echo "[5/5] 启动服务..."
echo ""
echo "  后端 API: http://localhost:8000"
echo "  API 文档: http://localhost:8000/api/docs"
echo "  前端页面: http://localhost:5173"
echo ""
echo "========================================"

# 启动后端（后台）
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

# 启动前端（前台）
npm run dev &
FRONTEND_PID=$!

echo "服务已启动！按 Ctrl+C 停止所有服务"

cleanup() {
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
