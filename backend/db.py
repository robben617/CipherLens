import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "cipherlens.db"
BACKUP_PREFIX = "cipherlens.db.bak-v0-"
BACKUP_KEEP = 2
TARGET_VERSION = 1
logger = logging.getLogger("cipherlens.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    mode TEXT NOT NULL,
    plaintext TEXT NOT NULL,
    "key" TEXT NOT NULL,
    key_bits INTEGER NOT NULL,
    anon_merged INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS step_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    step_index INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    dwell_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    step_index INTEGER NOT NULL,
    misconception_type TEXT NOT NULL,
    responded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    misconception_tag TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    item_id INTEGER NOT NULL REFERENCES quiz_items(id),
    submitted TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    first_diff_round INTEGER,
    first_diff_step INTEGER,
    first_diff_byte INTEGER
);

CREATE TABLE IF NOT EXISTS practice_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    submitted TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    first_diff_round INTEGER,
    first_diff_step TEXT,
    first_diff_step_index INTEGER,
    first_diff_byte INTEGER,
    misconception TEXT,
    client_id TEXT NOT NULL DEFAULT 'legacy-default',
    design_tag TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tutor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    step_index INTEGER NOT NULL,
    prompt_ver TEXT NOT NULL,
    model_ver TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    degraded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_practice_client ON practice_attempts(client_id)",
    "CREATE INDEX IF NOT EXISTS idx_practice_item ON practice_attempts(item_id)",
    "CREATE INDEX IF NOT EXISTS idx_step_events_session ON step_events(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_diagnoses_session ON diagnoses(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_attempts_item ON attempts(item_id)",
)


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def _read_user_version() -> int:
    if not DB_PATH.exists():
        return 0
    connection = sqlite3.connect(DB_PATH)
    try:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()


def _backup() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = DB_PATH.with_name(f"{BACKUP_PREFIX}{stamp}")
    shutil.copy2(DB_PATH, target)

    backups = sorted(
        DB_PATH.parent.glob(f"{BACKUP_PREFIX}*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for stale in backups[BACKUP_KEEP:]:
        stale.unlink(missing_ok=True)

    logger.info("database backup created path=%s", target.name)
    return target


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _migrate() -> None:
    connection = sqlite3.connect(DB_PATH, isolation_level=None)
    connection.row_factory = sqlite3.Row
    step = "start"
    try:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version >= TARGET_VERSION:
            return

        step = "wal"
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")

        step = "begin"
        connection.execute("BEGIN IMMEDIATE")

        step = "columns"
        columns = _column_names(connection, "practice_attempts")
        if "client_id" not in columns:
            connection.execute(
                "ALTER TABLE practice_attempts "
                "ADD COLUMN client_id TEXT NOT NULL DEFAULT 'legacy-default'"
            )
        if "design_tag" not in columns:
            connection.execute(
                "ALTER TABLE practice_attempts ADD COLUMN design_tag TEXT"
            )

        step = "indexes"
        for statement in INDEXES:
            connection.execute(statement)

        step = "verify"
        before = connection.execute(
            "SELECT COUNT(*) FROM practice_attempts"
        ).fetchone()[0]
        after = connection.execute(
            "SELECT COUNT(*) FROM practice_attempts"
        ).fetchone()[0]
        if before != after:
            raise RuntimeError(f"row count changed {before} -> {after}")

        step = "version"
        connection.execute(f"PRAGMA user_version = {TARGET_VERSION}")
        step = "commit"
        connection.execute("COMMIT")
        logger.info("database migrated user_version=%s", TARGET_VERSION)
    except Exception as error:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        logger.exception("database migration failed step=%s", step)
        raise RuntimeError(
            f"database migration failed at step={step}: {error}"
        ) from error
    finally:
        connection.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists() and _read_user_version() < TARGET_VERSION:
        _backup()

    with connect() as connection:
        connection.executescript(SCHEMA)
        connection.execute("PRAGMA journal_mode = WAL")

    _migrate()