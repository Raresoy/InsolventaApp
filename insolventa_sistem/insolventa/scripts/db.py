import sqlite3
from config.settings import DB_PATH


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create()

    def create(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS dosare (
            case_uid TEXT PRIMARY KEY,
            nr_dosar TEXT,
            debitor TEXT,
            nr_inregistrare TEXT,
            tribunal TEXT,
            data_inreg TEXT,
            status TEXT
        )
        """)
        self.conn.commit()

    def exists(self, uid):
        return self.conn.execute(
            "SELECT 1 FROM dosare WHERE case_uid=?",
            (uid,)
        ).fetchone() is not None

    def insert(self, d):
        self.conn.execute("""
        INSERT OR IGNORE INTO dosare VALUES (?,?,?,?,?,?,?)
        """, (
            d.case_uid,
            d.nr_dosar,
            d.debitor,
            d.nr_inregistrare,
            d.tribunal,
            d.data_inreg,
            "new"
        ))
        self.conn.commit()