from typing import Optional

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from engines.contracts import config

engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_engine() -> AsyncEngine:
    """懒加载创建并返回全局 MySQL 异步引擎单例。"""
    global engine
    if engine is None:
        engine = create_async_engine(url=_build_db_url(), echo=False)
    return engine


def _build_db_url() -> URL:
    """依据配置项拼接 MySQL 异步连接 URL。"""
    return URL.create(
        drivername="mysql+aiomysql",
        username=config.get_settings().DB_USER,
        password=config.get_settings().DB_PASSWORD,
        host=config.get_settings().DB_HOST,
        port=config.get_settings().DB_PORT,
        database=config.get_settings().DB_NAME,
    )


async def close_async_engine() -> None:
    """释放并清空全局 MySQL 异步引擎。"""
    global engine
    if engine is not None:
        try:
            await engine.dispose()
        finally:
            engine = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """懒加载创建绑定异步引擎的会话工厂。"""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_async_engine(), expire_on_commit=False)
    return _session_factory
