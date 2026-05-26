"""
schemas.py - Pydantic 模型定义
用于数据验证和序列化，已移除 EmailStr 强依赖，确保开箱即用。
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# ==========================================
# 通用响应模型
# ==========================================

class Message(BaseModel):
    """通用消息响应"""
    message: str


class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: Optional[int] = None


class PageParams(BaseModel):
    """分页参数"""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=12, ge=1, le=100)

    
class PageResponse(BaseModel):
    """分页响应"""
    data: List[object]
    count: int
    skip: int
    limit: int


# ==========================================
# 用户相关模型
# ==========================================

class UserBase(BaseModel):
    """用户基础模型（将 EmailStr 替换为 str，免去安装 email-validator 依赖）"""
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """用户注册请求"""
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """用户登录请求"""
    email: str
    password: str


class UserPublic(UserBase):
    """用户公开信息"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserUpdateMe(BaseModel):
    """更新当前用户信息"""
    full_name: Optional[str] = None
    email: Optional[str] = None


class UpdatePassword(BaseModel):
    """更新密码"""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ==========================================
# 景点相关模型
# ==========================================

class AttractionBase(BaseModel):
    """景点基础模型"""
    attraction_id: int
    city_name: str
    attraction_name: str
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    open_hours: Optional[str] = None
    ticket_price: Optional[float] = None
    overview: Optional[str] = None
    facilities: Optional[str] = None
    type: Optional[str] = None
    duration_of_visit: Optional[str] = None
    rate_of_restaurant: Optional[float] = None
    facilities_group: Optional[str] = None
    country: Optional[str] = None


class AttractionCreate(AttractionBase):
    """创建景点请求"""
    pass


class AttractionPublic(AttractionBase):
    """景点公开信息"""
    id: int
    created_at: datetime


class AttractionListResponse(BaseModel):
    """景点列表响应"""
    data: List[AttractionPublic]
    count: int


class AttractionFilterParams(BaseModel):
    """景点筛选参数"""
    city: Optional[str] = None
    type: Optional[str] = None
    search: Optional[str] = None


# ==========================================
# 收藏相关模型
# ==========================================

class BookmarkCreate(BaseModel):
    """收藏请求"""
    pass


class BookmarkPublic(BaseModel):
    """收藏信息"""
    id: int
    user_id: int
    attraction_id: int
    created_at: datetime

    # 关联的景点信息（可选）
    attraction: Optional[AttractionPublic] = None


class BookmarkListResponse(BaseModel):
    """收藏列表响应"""
    data: List[BookmarkPublic]
    count: int