from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from redis import Redis


class StateStore:
    backend_name = "memory"

    def load(self) -> dict[str, Any] | None:
        return None

    def save(self, payload: dict[str, Any]) -> None:
        return None


@dataclass
class RedisStateStore(StateStore):
    client: Redis
    key: str
    backend_name: str = "redis"

    def load(self) -> dict[str, Any] | None:
        payload = self.client.get(self.key)
        if not payload:
            return None
        return json.loads(payload)

    def save(self, payload: dict[str, Any]) -> None:
        self.client.set(self.key, json.dumps(payload))


def create_state_store() -> StateStore:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return StateStore()

    key = os.getenv("BLOCKCHAIN_STATE_KEY", "minimal-python-blockchain:state")
    client = Redis.from_url(redis_url, decode_responses=True)
    return RedisStateStore(client=client, key=key)
