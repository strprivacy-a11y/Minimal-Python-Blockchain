from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from psycopg import connect
from psycopg.rows import dict_row
from redis import Redis


class StateStore:
    backend_name = "memory"

    def load(self) -> dict[str, Any] | None:
        return None

    def save(self, payload: dict[str, Any]) -> None:
        return None

    def is_ready(self) -> tuple[bool, str]:
        return True, "memory store ready"


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

    def is_ready(self) -> tuple[bool, str]:
        try:
            self.client.ping()
        except Exception as error:
            return False, f"redis unavailable: {error}"
        return True, "redis ready"


@dataclass
class PostgresStateStore(StateStore):
    dsn: str
    key: str
    backend_name: str = "postgres"
    table_name: str = "blockchain_state"

    def __post_init__(self) -> None:
        self._ensure_table()

    def _connect(self):
        return connect(self.dsn, row_factory=dict_row)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        state_key TEXT PRIMARY KEY,
                        payload JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
            conn.commit()

    def load(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT payload FROM {self.table_name} WHERE state_key = %s",
                    (self.key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return row["payload"]

    def save(self, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} (state_key, payload, updated_at)
                    VALUES (%s, %s::jsonb, NOW())
                    ON CONFLICT (state_key)
                    DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                    """,
                    (self.key, json.dumps(payload)),
                )
            conn.commit()

    def is_ready(self) -> tuple[bool, str]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS ok")
                    row = cur.fetchone()
                    if not row or row["ok"] != 1:
                        return False, "postgres readiness query failed"
        except Exception as error:
            return False, f"postgres unavailable: {error}"
        return True, "postgres ready"


def create_state_store() -> StateStore:
    state_key = os.getenv("BLOCKCHAIN_STATE_KEY", "minimal-python-blockchain:state")
    redis_url = os.getenv("REDIS_URL", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()

    if redis_url:
        client = Redis.from_url(redis_url, decode_responses=True)
        return RedisStateStore(client=client, key=state_key)

    if database_url:
        return PostgresStateStore(dsn=database_url, key=state_key)

    return StateStore()
