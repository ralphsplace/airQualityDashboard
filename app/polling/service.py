from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.db.session import SessionLocal
from app.polling.clients import IndoorSourceClient, WAQISourceClient
from app.services.mappers import map_indoor_payload, map_outdoor_payload
from app.services.repository import AirRepository

logger = logging.getLogger(__name__)


class PollerService:
    def __init__(
        self,
        indoor_client: IndoorSourceClient,
        outdoor_client: WAQISourceClient,
        interval_seconds: int,
    ) -> None:
        self.indoor_client = indoor_client
        self.outdoor_client = outdoor_client
        self.interval_seconds = interval_seconds
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def poll_once(self) -> None:
        await asyncio.gather(self._poll_indoor(), self._poll_outdoor())

    async def _poll_indoor(self) -> None:
        try:
            payload = await self.indoor_client.fetch()
            mapped = map_indoor_payload(payload)
            with SessionLocal() as db:
                AirRepository(db).add_indoor_reading(mapped)
        except Exception:
            logger.exception("Indoor polling failed")

    async def _poll_outdoor(self) -> None:
        try:
            payload = await self.outdoor_client.fetch()
            mapped = map_outdoor_payload(payload)
            with SessionLocal() as db:
                AirRepository(db).add_outdoor_reading(mapped)
        except Exception:
            logger.exception("Outdoor polling failed")

    async def run(self) -> None:
        while not self._stop_event.is_set():
            await self.poll_once()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                pass

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None


def build_default_poller() -> PollerService:
    return PollerService(
        indoor_client=IndoorSourceClient(settings.indoor_source_url, settings.request_timeout_seconds),
        outdoor_client=WAQISourceClient(settings.waqi_base_url, settings.waqi_token, settings.request_timeout_seconds),
        interval_seconds=settings.poll_interval_seconds,
    )
