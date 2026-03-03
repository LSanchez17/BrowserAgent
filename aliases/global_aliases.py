from fastapi.params import Depends

from dependencies.dependencies import get_redis

# Global Aliases
RedisDepends = Depends(get_redis)