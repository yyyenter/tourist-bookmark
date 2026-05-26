"""
main.py - FastAPI 路由网关
负责接口暴露、请求拦截、参数校验及响应序列化
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# 导入底层驱动及统一的模型定义
from database import get_mysql_connection
import crud
# 统一使用标准的 schemas 架构，防止模型定义在项目中乱飞
from schemas import (
    UserCreate, UserLogin, UserPublic, Token,
    AttractionPublic, AttractionListResponse, PageParams, Message
)

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
# 依赖注入 (Dependency Injection)
# ==========================================
def get_db():
    """每个请求独立的数据库连接上下文寿命周期管理"""
    conn = get_mysql_connection()
    try:
        yield conn
    finally:
        conn.close()

# ==========================================
# 数据解析器 (Data Parsers)
# ==========================================
def parse_attraction(row: dict) -> dict:
    """将数据库 Dict 转换为符合规范的数据格式，防范数据类型 Shortcut"""
    return {
        "id": row["id"],
        "attraction_id": row["attraction_id"],
        "city_name": row["city_name"],
        "attraction_name": row["attraction_name"],
        "address": row.get("address"),
        "longitude": float(row["longitude"]) if row.get("longitude") else None,
        "latitude": float(row["latitude"]) if row.get("latitude") else None,
        "open_hours": row.get("open_hours"),
        "ticket_price": float(row["ticket_price"]) if row.get("ticket_price") else None,
        "overview": row.get("overview"),
        "facilities": row.get("facilities"),
        "type": row.get("type"),
        "duration_of_visit": row.get("duration_of_visit"),
        "rate_of_restaurant": float(row["rate_of_restaurant"]) if row.get("rate_of_restaurant") else None,
        "facilities_group": row.get("facilities_group"),
        "country": row.get("country"),
        "created_at": row.get("created_at") # 这里的 datetime 会由 Pydantic 自动转换为标准的 ISO 字符串
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

@app.get('/api/attractions/{attraction_id}', response_model=AttractionPublic)
def get_attraction(attraction_id: int, db=Depends(get_db)):
    """根据主键 ID 获取具体的景点元数据"""
    result = crud.get_attraction_by_id(db, attraction_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")
    return parse_attraction(result)

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

    # 2. 密码加密占位（安全机制重构区）
    # TODO: 实际生产中必须引入 passlib/bcrypt 进行加盐哈希：hashed_password = pwd_context.hash(user.password)
    hashed_password = user.password 

    # 3. 落地落库
    user_id = crud.create_user(db, email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    
    # 重新构建干净的返回数据
    from datetime import datetime
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

    # TODO: 生产中验证密码：if not pwd_context.verify(user.password, db_user['hashed_password'])
    
    # TODO: 签发标准的安全签名 JWT Token而非假数据
    access_token = f"fake-jwt-token-for-user-{db_user['id']}" 

    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# 权限挂起与未完成设计 (AOP 鉴权区)
# ==========================================
@app.get('/api/bookmarks', response_model=Message)
def get_bookmarks(token: str = Depends(oauth2_scheme)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Token Verification pending")

@app.post('/api/bookmarks/{attraction_id}', response_model=Message)
def add_bookmark(attraction_id: int, token: str = Depends(oauth2_scheme)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Auth integration required")

@app.delete('/api/bookmarks/{attraction_id}', response_model=Message)
def remove_bookmark(attraction_id: int, token: str = Depends(oauth2_scheme)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Auth integration required")

@app.get('/api/me', response_model=UserPublic)
def get_current_user(token: str = Depends(oauth2_scheme)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User context parsing pending")