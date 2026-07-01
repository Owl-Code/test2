import sqlite3
import hashlib
import json
import os
from typing import List, Dict, Any, Optional

class SwarmHistoryDB:
    """Manages SQLite database storage for swarm checkpoint histories with SHA256 integrity audits."""
    
    def __init__(self, db_path: str = "./artifacts/checkpoints/swarm_history.db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    tick INTEGER PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    emergence REAL NOT NULL
                )
            """)
            conn.commit()

    def save_checkpoint(self, tick: int, state_dict: Dict[str, Any], emergence: float) -> str:
        """Serializes the state dict, hashes it, and saves it into the SQLite database."""
        state_json = json.dumps(state_dict, sort_keys=True)
        sha256_hash = hashlib.sha256(state_json.encode("utf-8")).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints (tick, state_json, sha256_hash, emergence) VALUES (?, ?, ?, ?)",
                (tick, state_json, sha256_hash, emergence)
            )
            conn.commit()
        return sha256_hash

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieves a summary of all saved ticks, emergence scores, and SHA256 hashes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tick, sha256_hash, emergence FROM checkpoints ORDER BY tick ASC")
            rows = cursor.fetchall()
            
        return [
            {"tick": row[0], "hash": row[1], "emergence": row[2]}
            for row in rows
        ]

    def load_checkpoint(self, tick: int) -> Optional[Dict[str, Any]]:
        """Loads a checkpoint by tick, audits its SHA256 integrity, and returns the state dictionary."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json, sha256_hash FROM checkpoints WHERE tick = ?", (tick,))
            row = cursor.fetchone()
            
        if not row:
            return None
            
        state_json, stored_hash = row
        computed_hash = hashlib.sha256(state_json.encode("utf-8")).hexdigest()
        if computed_hash != stored_hash:
            raise ValueError(f"Integrity check failed: Checkpoint for tick {tick} has been mutated on disk!")
            
        return json.loads(state_json)
