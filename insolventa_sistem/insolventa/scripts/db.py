import sqlite3
from datetime import datetime
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
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS contor (
            an INTEGER PRIMARY KEY,
            valoare INTEGER DEFAULT 0
        )
        """)
        self.conn.commit()

    def next_nr_inregistrare(self):
        an = datetime.now().year
        self.conn.execute("""
            INSERT INTO contor (an, valoare) VALUES (?, 1)
            ON CONFLICT(an) DO UPDATE SET valoare = valoare + 1
        """, (an,))
        self.conn.commit()
        row = self.conn.execute(
            "SELECT valoare FROM contor WHERE an=?", (an,)
        ).fetchone()
        return f"{row[0]}/{an}"

    def exists(self, uid):
        return self.conn.execute(
            "SELECT 1 FROM dosare WHERE case_uid=?", (uid,)
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

    def mark_processed(self, uid):
        self.conn.execute(
            "UPDATE dosare SET status=? WHERE case_uid=?",
            ("sent", uid)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()