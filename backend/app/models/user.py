# -*- coding: utf-8 -*-
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user")  # "admin" or "user"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ProjectShare(Base):
    __tablename__ = "project_shares"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    permission = Column(String(10), default="view")  # "view" or "edit"
    created_at = Column(DateTime, server_default=func.now())
