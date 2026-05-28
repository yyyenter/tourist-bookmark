"""
main.py - FastAPI 路由网关
负责接口暴露、请求拦截、参数校验及响应序列化
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt

# 导入底层驱动及统一的模型定义
from database import get_db
import crud
# 统一使用标准的 schemas 架构，防止模型定义在项目中乱飞
from schemas import (
    UserCreate, UserLogin, UserPublic, Token,
    AttractionPublic, AttractionListResponse, PageParams, Message
)

# ==========================================
# JWT 配置
# ==========================================
# 密钥（生产环境应从环境变量读取）
SECRET_KEY = "your-super-secret-key-change-in-production-123456789"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时

app = FastAPI(
    title="旅游助手 API",
    description="提供高并发景点检索、智能路由、用户收藏管理等服务",
    version="2.2.0",
    docs_url="/api/docs",
    redoc_url=None,
    debug=True
)

# 跨域资源共享配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175","http://localhost:5174", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# ==========================================
# 辅助函数
# ==========================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> int:
    """验证 JWT Token 并返回 user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return int(user_id_str)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ==========================================
# 依赖注入 (Dependency Injection)
# get_db 已从 database 模块导入，直接使用
# ==========================================


# ==========================================
# 数据解析器 (Data Parsers)
# ==========================================
def parse_attraction(row) -> dict:
    """将数据库 Row 转换为符合规范的数据格式（兼容 sqlite3.Row 和 dict）"""
    # SQLite Row 对象不支持 .get()，先转为 dict
    if not isinstance(row, dict):
        d = dict(row)
    else:
        d = row
    return {
        "id": d["id"],
        "attraction_id": d["attraction_id"],
        "city_name": d["city_name"],
        "attraction_name": d["attraction_name"],
        "address": d.get("address"),
        "longitude": float(d["longitude"]) if d.get("longitude") else None,
        "latitude": float(d["latitude"]) if d.get("latitude") else None,
        "open_hours": d.get("open_hours"),
        "ticket_price": float(d["ticket_price"]) if d.get("ticket_price") else None,
        "overview": d.get("overview"),
        "facilities": d.get("facilities"),
        "type": d.get("type"),
        "duration_of_visit": d.get("duration_of_visit"),
        "rate_of_restaurant": float(d["rate_of_restaurant"]) if d.get("rate_of_restaurant") else None,
        "facilities_group": d.get("facilities_group"),
        "country": d.get("country"),
        "created_at": d.get("created_at")
    }


# ==========================================
# 景点相关 API (聚合路由器)
# ==========================================

@app.get('/api/attractions', response_model=AttractionListResponse)
def get_attractions(
    params: PageParams = Depends(),
    city: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    db=Depends(get_db)
):
    """
    获取景点列表（核心多路交叉检索接口）
    由原来的原生长 SQL 彻底解耦至 crud 模块中，支持无缝添加多模态语义过滤器
    """
    results, count = crud.fetch_attractions(
        db, limit=params.limit, skip=params.skip, city=city, attraction_type=type, search=search
    )
    return {"data": [parse_attraction(r) for r in results], "count": count}

@app.get('/api/attractions/{id}', response_model=AttractionPublic)
def get_attraction(id: int, db=Depends(get_db)):
    """根据主键 ID 获取具体的景点元数据（含相关交通路线）"""
    result = crud.get_attraction_by_id(db, id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

    # 获取相关交通路线（转为普通 dict）
    transport_routes = [dict(r) for r in crud.get_transport_routes_by_city(db, result["city_name"])]

    # 解析景点数据并添加交通信息
    attraction_data = parse_attraction(result)
    attraction_data["transport_routes"] = transport_routes
    return attraction_data

@app.get('/api/attractions/city/{city}', response_model=AttractionListResponse)
def get_attractions_by_city(city: str, params: PageParams = Depends(), db=Depends(get_db)):
    """分类路由：按城市名高精准度聚类筛选景点"""
    results, count = crud.fetch_attractions(db, limit=params.limit, skip=params.skip, city=city)
    return {"data": [parse_attraction(r) for r in results], "count": count}

@app.get('/api/attractions/type/{type}', response_model=AttractionListResponse)
def get_attractions_by_type(type: str, params: PageParams = Depends(), db=Depends(get_db)):
    """分类路由：按具体旅游业态/标签类型筛选景点"""
    results, count = crud.fetch_attractions(db, limit=params.limit, skip=params.skip, attraction_type=type)
    return {"data": [parse_attraction(r) for r in results], "count": count}


# ==========================================
# 用户相关认证 API
# ==========================================

@app.post('/api/register', response_model=UserPublic)
def register(user: UserCreate, db=Depends(get_db)):
    """新用户注册接入端点"""
    # 1. 校验邮箱冲突
    if crud.check_user_exists_by_email(db, user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # 2. 密码哈希（使用 bcrypt）
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 3. 落地落库
    user_id = crud.create_user(db, email=user.email, hashed_password=hashed_password, full_name=user.full_name)

    # 重新构建干净的返回数据
    return {
        "id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now()
    }


@app.post('/api/login', response_model=Token)
def login(user: UserLogin, db=Depends(get_db)):
    """用户身份质询，颁发 Bearer Token"""
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    # 验证密码
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user['hashed_password'].encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    # 生成 JWT Token（包含 user_id 在 subject 字段）
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user['id'])},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 认证依赖（使用标准 JWT 解析）
# ==========================================

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    从标准 JWT Token 中提取当前用户 ID
    """
    return verify_token(token)


@app.get('/api/bookmarks')
def get_bookmarks(current_user_id: int = Depends(get_current_user_id), db=Depends(get_db)):
    """获取当前登录用户的所有收藏景点（带详情）"""
    results = crud.get_user_bookmarks_with_details(db, current_user_id)
    return {"data": [dict(r) for r in results], "count": len(results)}

@app.post('/api/bookmarks/{attraction_id}')
def add_bookmark(attraction_id: int, current_user_id: int = Depends(get_current_user_id), db=Depends(get_db)):
    """执行收藏动作"""
    # 检查景点是否存在
    attraction = crud.get_attraction_by_id(db, attraction_id)
    if not attraction:
        raise HTTPException(status_code=404, detail="景点不存在")

    success = crud.add_bookmark(db, current_user_id, attraction_id)
    if success:
        return {"message": "收藏成功"}
    return {"message": "已经收藏过该景点"}

@app.delete('/api/bookmarks/{attraction_id}')
def remove_bookmark(attraction_id: int, current_user_id: int = Depends(get_current_user_id), db=Depends(get_db)):
    """取消收藏"""
    success = crud.remove_bookmark(db, current_user_id, attraction_id)
    if success:
        return {"message": "取消收藏成功"}
    raise HTTPException(status_code=404, detail="未找到对应的收藏记录")

@app.get('/api/me', response_model=UserPublic)
def get_current_user(current_user_id: int = Depends(get_current_user_id), db=Depends(get_db)):
    """获取个人基本信息"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (current_user_id,))
    user = cursor.fetchone()
    cursor.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)
