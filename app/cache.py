"""
内存级高命中壁纸缓存模块
"""

import time
import hashlib
from collections import OrderedDict
from typing import Optional, Tuple

class MemoryWallpaperCache:
    def __init__(self, max_size: int = 500, ttl_seconds: int = 86400):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache = OrderedDict()

    def _generate_key(self, params: dict) -> str:
        raw_str = "|".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.md5(raw_str.encode("utf-8")).hexdigest()

    def get(self, params: dict) -> Optional[Tuple[bytes, str]]:
        key = self._generate_key(params)
        now = time.time()
        if key in self._cache:
            data, expire_at, etag = self._cache[key]
            if now < expire_at:
                self._cache.move_to_end(key)
                return data, etag
            else:
                del self._cache[key]
        return None

    def set(self, params: dict, data: bytes) -> str:
        key = self._generate_key(params)
        etag = f'W/"{hashlib.sha256(data).hexdigest()[:16]}"'
        now = time.time()
        expire_at = now + self.ttl

        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = (data, expire_at, etag)
        return etag

WALLPAPER_CACHE = MemoryWallpaperCache()
