"""Object-oriented wrapper for database connection details."""

from dataclasses import dataclass
import sqlite3


@dataclass
class Database:
    path: str

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def test_connection(self) -> bool:
        conn = self.connect()
        try:
            conn.execute("SELECT 1")
            return True
        finally:
            conn.close()
