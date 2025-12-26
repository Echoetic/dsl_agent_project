#!/usr/bin/env python3
"""
用户认证模块
提供用户注册、登录、会话管理功能
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class AuthError(Exception):
    """认证异常"""
    pass


class UserRole(Enum):
    """用户角色"""
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """用户数据类"""
    user_id: str
    username: str
    password_hash: str
    email: str
    role: str = "user"
    created_at: str = ""
    last_login: str = ""
    is_active: bool = True
    
    def to_dict(self) -> dict:
        """转换为字典（不包含密码）"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "is_active": self.is_active
        }


@dataclass
class Session:
    """会话数据类"""
    session_id: str
    user_id: str
    created_at: float
    expires_at: float
    ip_address: str = ""
    user_agent: str = ""


class PasswordHasher:
    """密码哈希工具"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """
        哈希密码
        返回: (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # 简化版本：使用SHA256 + salt
        combined = salt_bytes + password_bytes
        for _ in range(10000):  # 迭代增加破解难度
            combined = hashlib.sha256(combined).digest()
        
        password_hash = salt + ":" + combined.hex()
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, _ = password_hash.split(":", 1)
            new_hash, _ = PasswordHasher.hash_password(password, salt)
            return secrets.compare_digest(new_hash, password_hash)
        except Exception:
            return False


class UserStore:
    """用户存储（基于JSON文件）"""
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            data_file = os.path.join(data_dir, 'users.json')
        
        self.data_file = data_file
        self._load_data()
    
    def _load_data(self):
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.users = data.get('users', {})
            except Exception:
                self.users = {}
        else:
            self.users = {}
            self._save_data()
    
    def _save_data(self):
        """保存用户数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({'users': self.users}, f, ensure_ascii=False, indent=2)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user_data in self.users.values():
            if user_data['username'] == username:
                return User(**user_data)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        for user_data in self.users.values():
            if user_data['email'] == email:
                return User(**user_data)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        if user_id in self.users:
            return User(**self.users[user_id])
        return None
    
    def create_user(self, user: User) -> bool:
        """创建用户"""
        if user.user_id in self.users:
            return False
        
        self.users[user.user_id] = asdict(user)
        self._save_data()
        return True
    
    def update_user(self, user: User) -> bool:
        """更新用户"""
        if user.user_id not in self.users:
            return False
        
        self.users[user.user_id] = asdict(user)
        self._save_data()
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id not in self.users:
            return False
        
        del self.users[user_id]
        self._save_data()
        return True


class SessionManager:
    """会话管理器"""
    
    def __init__(self, session_timeout: int = 3600):
        """
        初始化会话管理器
        session_timeout: 会话超时时间（秒），默认1小时
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
    
    def create_session(self, user_id: str, ip_address: str = "", user_agent: str = "") -> str:
        """创建新会话"""
        session_id = secrets.token_urlsafe(32)
        now = time.time()
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + self.session_timeout,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session is None:
            return None
        
        # 检查是否过期
        if time.time() > session.expires_at:
            self.destroy_session(session_id)
            return None
        
        return session
    
    def refresh_session(self, session_id: str) -> bool:
        """刷新会话（延长过期时间）"""
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.expires_at = time.time() + self.session_timeout
        return True
    
    def destroy_session(self, session_id: str) -> bool:
        """销毁会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_user_sessions(self, user_id: str) -> list:
        """获取用户的所有会话"""
        return [s for s in self.sessions.values() if s.user_id == user_id]
    
    def destroy_user_sessions(self, user_id: str):
        """销毁用户的所有会话"""
        session_ids = [s.session_id for s in self.sessions.values() if s.user_id == user_id]
        for session_id in session_ids:
            self.destroy_session(session_id)
    
    def cleanup_expired(self):
        """清理过期会话"""
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now > s.expires_at]
        for session_id in expired:
            del self.sessions[session_id]


class AuthService:
    """认证服务"""
    
    def __init__(self, user_store: UserStore = None, session_manager: SessionManager = None):
        self.user_store = user_store or UserStore()
        self.session_manager = session_manager or SessionManager()
        self.hasher = PasswordHasher()
    
    def register(self, username: str, password: str, email: str) -> Tuple[bool, str, Optional[User]]:
        """
        用户注册
        返回: (success, message, user)
        """
        # 验证输入
        if not username or len(username) < 3:
            return False, "用户名至少需要3个字符", None
        
        if not password or len(password) < 6:
            return False, "密码至少需要6个字符", None
        
        if not email or "@" not in email:
            return False, "请输入有效的邮箱地址", None
        
        # 检查用户名是否已存在
        if self.user_store.get_user_by_username(username):
            return False, "用户名已被注册", None
        
        # 检查邮箱是否已存在
        if self.user_store.get_user_by_email(email):
            return False, "邮箱已被注册", None
        
        # 创建用户
        user_id = secrets.token_urlsafe(16)
        password_hash, _ = self.hasher.hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            email=email,
            role=UserRole.USER.value,
            created_at=datetime.now().isoformat(),
            last_login="",
            is_active=True
        )
        
        if self.user_store.create_user(user):
            return True, "注册成功", user
        else:
            return False, "注册失败，请稍后重试", None
    
    def login(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Tuple[bool, str, Optional[str], Optional[User]]:
        """
        用户登录
        返回: (success, message, session_id, user)
        """
        # 验证输入
        if not username or not password:
            return False, "请输入用户名和密码", None, None
        
        # 查找用户
        user = self.user_store.get_user_by_username(username)
        if user is None:
            return False, "用户名或密码错误", None, None
        
        # 验证密码
        if not self.hasher.verify_password(password, user.password_hash):
            return False, "用户名或密码错误", None, None
        
        # 检查账户状态
        if not user.is_active:
            return False, "账户已被禁用", None, None
        
        # 更新最后登录时间
        user.last_login = datetime.now().isoformat()
        self.user_store.update_user(user)
        
        # 创建会话
        session_id = self.session_manager.create_session(user.user_id, ip_address, user_agent)
        
        return True, "登录成功", session_id, user
    
    def logout(self, session_id: str) -> Tuple[bool, str]:
        """
        用户登出
        返回: (success, message)
        """
        if self.session_manager.destroy_session(session_id):
            return True, "登出成功"
        else:
            return False, "会话不存在"
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[User]]:
        """
        验证会话
        返回: (is_valid, user)
        """
        session = self.session_manager.get_session(session_id)
        if session is None:
            return False, None
        
        user = self.user_store.get_user_by_id(session.user_id)
        if user is None or not user.is_active:
            self.session_manager.destroy_session(session_id)
            return False, None
        
        # 刷新会话
        self.session_manager.refresh_session(session_id)
        
        return True, user
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        修改密码
        返回: (success, message)
        """
        user = self.user_store.get_user_by_id(user_id)
        if user is None:
            return False, "用户不存在"
        
        # 验证旧密码
        if not self.hasher.verify_password(old_password, user.password_hash):
            return False, "原密码错误"
        
        # 验证新密码
        if len(new_password) < 6:
            return False, "新密码至少需要6个字符"
        
        # 更新密码
        user.password_hash, _ = self.hasher.hash_password(new_password)
        self.user_store.update_user(user)
        
        # 销毁该用户的所有会话（强制重新登录）
        self.session_manager.destroy_user_sessions(user_id)
        
        return True, "密码修改成功，请重新登录"
    
    def get_current_user(self, session_id: str) -> Optional[User]:
        """获取当前登录用户"""
        is_valid, user = self.validate_session(session_id)
        return user if is_valid else None


# 全局认证服务实例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务单例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
