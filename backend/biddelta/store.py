"""SQLite aggregate snapshots: atomic writes, immutable history, original bytes."""
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from .models import Packet


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    packet_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    body TEXT NOT NULL, PRIMARY KEY(packet_id, sequence));
                CREATE TABLE IF NOT EXISTS sources (
                    packet_id TEXT NOT NULL, document_id TEXT NOT NULL,
                    content BLOB NOT NULL, PRIMARY KEY(packet_id, document_id));
                CREATE TRIGGER IF NOT EXISTS snapshots_no_update BEFORE UPDATE ON snapshots
                    BEGIN SELECT RAISE(ABORT, 'immutable snapshot'); END;
                CREATE TRIGGER IF NOT EXISTS snapshots_no_delete BEFORE DELETE ON snapshots
                    BEGIN SELECT RAISE(ABORT, 'immutable snapshot'); END;
                CREATE TRIGGER IF NOT EXISTS sources_no_update BEFORE UPDATE ON sources
                    BEGIN SELECT RAISE(ABORT, 'immutable source'); END;
                CREATE TRIGGER IF NOT EXISTS sources_no_delete BEFORE DELETE ON sources
                    BEGIN SELECT RAISE(ABORT, 'immutable source'); END;
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def load(db, packet_id: str, actor: str):
        row = db.execute('SELECT sequence,body FROM snapshots WHERE packet_id=? ORDER BY sequence DESC LIMIT 1',
                         (packet_id,)).fetchone()
        if row is None:
            raise KeyError(packet_id)
        packet = Packet.model_validate_json(row[1])
        if packet.owner_id != actor:
            raise PermissionError("Packet owner required")
        return row[0], packet

    def get(self, packet_id: str, actor: str) -> Packet:
        with self.connect() as db:
            return self.load(db, packet_id, actor)[1]

    @contextmanager
    def edit(self, packet_id: str, actor: str, expected_revision: int):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            seq, packet = self.load(db, packet_id, actor)
            if packet.revision != expected_revision:
                raise ValueError("Stale packet revision")
            yield db, packet
            db.execute('INSERT INTO snapshots VALUES (?,?,?)',
                       (packet.id, seq + 1, packet.model_dump_json()))

    def source_bytes(self, packet_id: str, document_id: str, actor: str) -> bytes:
        with self.connect() as db:
            self.load(db, packet_id, actor)
            row = db.execute('SELECT content FROM sources WHERE packet_id=? AND document_id=?',
                             (packet_id, document_id)).fetchone()
            if row is None:
                raise KeyError(document_id)
            return row[0]
