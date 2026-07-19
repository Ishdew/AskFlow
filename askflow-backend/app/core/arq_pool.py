from typing import Optional

from arq import create_pool, ArqRedis
from arq.connections import RedisSettings

from app.core.config import settings

# Set once by app.main's lifespan on startup. Deliberately not imported
# directly by other modules (that would freeze the `None` seen at their own
# import time, before the lifespan runs) - always go through get_arq_pool().
_arq_pool: Optional[ArqRedis] = None


async def init_arq_pool() -> None:
    global _arq_pool
    _arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))


async def close_arq_pool() -> None:
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.aclose()
        _arq_pool = None


def get_arq_pool() -> ArqRedis:
    if _arq_pool is None:
        raise RuntimeError("Arq pool accessed before startup / after shutdown")
    return _arq_pool
