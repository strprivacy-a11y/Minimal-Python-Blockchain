from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from time import time
from typing import Any
from urllib.parse import urlparse

import requests

from app.storage import StateStore


@dataclass
class Blockchain:
    node_id: str
    difficulty_prefix: str = "0000"
    state_store: StateStore = field(default_factory=StateStore)
    chain: list[dict[str, Any]] = field(default_factory=list)
    current_transactions: list[dict[str, Any]] = field(default_factory=list)
    nodes: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        persisted_state = self.state_store.load()
        if persisted_state:
            self.chain = persisted_state.get("chain", [])
            self.current_transactions = persisted_state.get("current_transactions", [])
            self.nodes = set(persisted_state.get("nodes", []))

        if not self.chain:
            self.create_block(proof=100, previous_hash="1")
        else:
            self._persist_state()

    def _persist_state(self) -> None:
        self.state_store.save(
            {
                "chain": self.chain,
                "current_transactions": self.current_transactions,
                "nodes": sorted(self.nodes),
            }
        )

    def register_node(self, address: str) -> str:
        normalized = self.normalize_node_address(address)
        self.nodes.add(normalized)
        self._persist_state()
        return normalized

    @staticmethod
    def normalize_node_address(address: str) -> str:
        parsed = urlparse(address if "://" in address else f"http://{address}")
        if not parsed.netloc:
            raise ValueError("Invalid node address")
        return f"{parsed.scheme}://{parsed.netloc}"

    def create_block(self, proof: int, previous_hash: str | None = None) -> dict[str, Any]:
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions.copy(),
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        self._persist_state()
        return block

    def create_transaction(self, sender: str, recipient: str, amount: float) -> int:
        self.current_transactions.append(
            {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
            }
        )
        self._persist_state()
        return self.last_block["index"] + 1

    @property
    def last_block(self) -> dict[str, Any]:
        return self.chain[-1]

    @staticmethod
    def hash(block: dict[str, Any]) -> str:
        encoded_block = str(sorted(block.items())).encode("utf-8")
        return sha256(encoded_block).hexdigest()

    def proof_of_work(self, previous_proof: int) -> int:
        proof = 0
        while not self.is_valid_proof(previous_proof, proof):
            proof += 1
        return proof

    def is_valid_proof(self, previous_proof: int, proof: int) -> bool:
        guess = f"{previous_proof}{proof}".encode("utf-8")
        guess_hash = sha256(guess).hexdigest()
        return guess_hash.startswith(self.difficulty_prefix)

    def is_valid_chain(self, chain: list[dict[str, Any]]) -> bool:
        if not chain:
            return False

        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block["previous_hash"] != self.hash(previous_block):
                return False

            if not self.is_valid_proof(previous_block["proof"], block["proof"]):
                return False

            previous_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        replaced = False
        max_length = len(self.chain)

        for node in self.nodes:
            response = requests.get(f"{node}/chain", timeout=5)
            if response.status_code != 200:
                continue

            payload = response.json()
            length = payload.get("length")
            chain = payload.get("chain")

            if isinstance(length, int) and isinstance(chain, list):
                if length > max_length and self.is_valid_chain(chain):
                    max_length = length
                    self.chain = chain
                    replaced = True

        if replaced:
            self._persist_state()

        return replaced
