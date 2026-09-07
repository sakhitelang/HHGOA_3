"""Simulated hash-chain blockchain: {timestamp, sha256(data), previous_hash}."""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

CHAIN_PATH = Path(__file__).resolve().parent.parent / "data" / "chain.json"


@dataclass
class Block:
    index: int
    timestamp: str
    data_hash: str
    previous_hash: str
    metadata: dict

    def block_hash(self) -> str:
        payload = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "data_hash": self.data_hash,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


class SimulatedChain:
    GENESIS = "0" * 64

    def __init__(self, path: Path = CHAIN_PATH):
        self.path = path
        self.blocks: list[Block] = []
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path) as f:
                raw = json.load(f)
            self.blocks = [Block(**b) for b in raw.get("blocks", [])]

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(
                {"blocks": [asdict(b) for b in self.blocks], "chain_type": "simulated_hash_chain"},
                f,
                indent=2,
            )

    def add_block(self, data_hash: str, metadata: dict) -> Block:
        prev = self.blocks[-1].block_hash() if self.blocks else self.GENESIS
        block = Block(
            index=len(self.blocks),
            timestamp=datetime.now(timezone.utc).isoformat(),
            data_hash=data_hash,
            previous_hash=prev,
            metadata=metadata,
        )
        self.blocks.append(block)
        self._save()
        return block

    def latest(self) -> Optional[Block]:
        return self.blocks[-1] if self.blocks else None

    def verify_chain_integrity(self) -> bool:
        prev_hash = self.GENESIS
        for block in self.blocks:
            if block.previous_hash != prev_hash:
                return False
            prev_hash = block.block_hash()
        return True

    def find_by_url(self, url: str) -> Optional[Block]:
        for block in reversed(self.blocks):
            if block.metadata.get("url") == url:
                return block
        return None
