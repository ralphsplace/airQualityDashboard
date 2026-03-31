from __future__ import annotations

from urllib.parse import urlencode

import httpx


class IndoorSourceClient:
    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    async def fetch(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url)
            response.raise_for_status()
            return response.json()


class WAQISourceClient:
    def __init__(self, base_url: str, token: str, timeout: float = 15.0) -> None:
        self.base_url = base_url
        self.token = token
        self.timeout = timeout

    async def fetch(self) -> dict:
        params = urlencode({"token": self.token})
        separator = "&" if "?" in self.base_url else "?"
        url = f"{self.base_url}{separator}{params}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
