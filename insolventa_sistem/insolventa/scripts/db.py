import sqlite3
from datetime import datetime

from config.settings import DB_PATH


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(
            DB_PATH,
            timeout=30,
        )

        self.conn.row_factory = sqlite3.Row

        # Mai sigur pentru acces concurent
        self.conn.execute("PRAGMA journal_mode=WAL")

        self.create_tables()

    def create_tables(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dosare (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                case_uid TEXT UNIQUE NOT NULL,

                nr_dosar TEXT NOT NULL,
                debitor TEXT,
                nr_inregistrare TEXT,
                tribunal TEXT,
                data_inreg TEXT,

                status TEXT DEFAULT 'detected',

                email_trimisa INTEGER DEFAULT 0,

                created_at TEXT,
                updated_at TEXT,

                eroare TEXT
            )
            """
        )

        self.conn.commit()

    def dosar_exista(self, case_uid: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1
            FROM dosare
            WHERE case_uid = ?
            """,
            (case_uid,),
        ).fetchone()

        return row is not None

    def insert_dosar(self, dosar, status="completed"):
        """
        Inserează dosarul sau îl ignoră dacă există deja.
        """

        now = datetime.now().isoformat()

        self.conn.execute(
            """
            INSERT OR IGNORE INTO dosare (
                case_uid,
                nr_dosar,
                debitor,
                nr_inregistrare,
                tribunal,
                data_inreg,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dosar.case_uid,
                dosar.nr_dosar,
                dosar.debitor,
                dosar.nr_inregistrare,
                dosar.tribunal,
                dosar.data_inreg,
                status,
                now,
                now,
            ),
        )

        self.conn.commit()

    def update_status(
        self,
        case_uid: str,
        status: str,
        eroare: str | None = None,
    ):
        """
        Actualizează statusul unui dosar existent.
        """

        self.conn.execute(
            """
            UPDATE dosare
            SET
                status = ?,
                eroare = ?,
                updated_at = ?
            WHERE case_uid = ?
            """,
            (
                status,
                eroare,
                datetime.now().isoformat(),
                case_uid,
            ),
        )

        self.conn.commit()

    def save_error(self, dosar, eroare: str):
        """
        Salvează eroarea chiar dacă dosarul nu există încă.
        """

        now = datetime.now().isoformat()

        self.conn.execute(
            """
            INSERT INTO dosare (
                case_uid,
                nr_dosar,
                debitor,
                nr_inregistrare,
                tribunal,
                data_inreg,
                status,
                created_at,
                updated_at,
                eroare
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(case_uid)
            DO UPDATE SET
                status = excluded.status,
                eroare = excluded.eroare,
                updated_at = excluded.updated_at
            """,
            (
                dosar.case_uid,
                dosar.nr_dosar,
                dosar.debitor,
                dosar.nr_inregistrare,
                dosar.tribunal,
                dosar.data_inreg,
                "failed",
                now,
                now,
                eroare,
            ),
        )

        self.conn.commit()

    def close(self):
        self.conn.close()