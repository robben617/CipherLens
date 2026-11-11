import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "cipherlens.db"
BACKUP_PREFIX = "cipherlens.db.bak-v0-"
BACKUP_KEEP = 2
TARGET_VERSION = 3
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
    client_id TEXT NOT NULL DEFAULT 'legacy-default',
    event_type TEXT NOT NULL,
    step_index INTEGER,
    dwell_ms INTEGER NOT NULL DEFAULT 0,
    at INTEGER,
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
    item_code TEXT,
    type TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    misconception_tag TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    plaintext_hex TEXT,
    key_hex TEXT,
    key_bits INTEGER
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    client_id TEXT NOT NULL DEFAULT 'legacy-default',
    item_id INTEGER NOT NULL REFERENCES quiz_items(id),
    submitted TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    first_diff_round INTEGER,
    first_diff_step TEXT,
    first_diff_step_index INTEGER,
    first_diff_byte INTEGER,
    source_bytes TEXT,
    design_tag TEXT,
    misconception TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    trace_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    question TEXT NOT NULL,
    source TEXT NOT NULL,
    model TEXT,
    latency_ms INTEGER NOT NULL,
    tokens INTEGER NOT NULL DEFAULT 0,
    degraded INTEGER NOT NULL DEFAULT 0,
    fabricated INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_practice_client ON practice_attempts(client_id)",
    "CREATE INDEX IF NOT EXISTS idx_practice_item ON practice_attempts(item_id)",
    "CREATE INDEX IF NOT EXISTS idx_step_events_client ON step_events(client_id)",
    "CREATE INDEX IF NOT EXISTS idx_diagnoses_session ON diagnoses(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_attempts_item ON attempts(item_id)",
    "CREATE INDEX IF NOT EXISTS idx_attempts_client ON attempts(client_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_quiz_item_code ON quiz_items(item_code)",
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


def _rebuild_tutor_logs(connection: sqlite3.Connection) -> None:
    """把 v1 的 tutor_logs 换成以 trace_id 为主键维度的审计表。

    旧表要求 `session_id NOT NULL`，但提问请求只带 trace_id（会话表压根没写），
    所以它从建库起就不可能被写入。SQLite 改不了 NOT NULL，只能重建；
    旧表本来就 0 行，真要是有行也原样搬到 `legacy` 名下，不丢记录。
    """
    columns = _column_names(connection, "tutor_logs")
    if "trace_id" in columns:
        return

    legacy_rows = []
    if columns:
        legacy_rows = connection.execute(
            "SELECT step_index, model_ver, latency_ms, degraded FROM tutor_logs"
        ).fetchall()

    connection.execute("ALTER TABLE tutor_logs RENAME TO tutor_logs_v1")
    connection.execute(
        """
        CREATE TABLE tutor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            question TEXT NOT NULL,
            source TEXT NOT NULL,
            model TEXT,
            latency_ms INTEGER NOT NULL,
            tokens INTEGER NOT NULL DEFAULT 0,
            degraded INTEGER NOT NULL DEFAULT 0,
            fabricated INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for row in legacy_rows:
        connection.execute(
            "INSERT INTO tutor_logs "
            "(trace_id, step_index, question, source, model, latency_ms, tokens, degraded, fabricated) "
            "VALUES ('legacy', ?, '', 'local', ?, ?, 0, ?, 0)",
            (
                row["step_index"],
                row["model_ver"],
                row["latency_ms"],
                row["degraded"],
            ),
        )
    connection.execute("DROP TABLE tutor_logs_v1")
    logger.info("tutor_logs rebuilt rows_kept=%s", len(legacy_rows))


def _add_columns(connection: sqlite3.Connection, table: str, columns) -> None:
    existing = _column_names(connection, table)
    for name, kind in columns:
        if name not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")


def _rebuild_attempts(connection: sqlite3.Connection) -> None:
    """给 attempts 补 client_id / design_tag / source_bytes / created_at。

    `attempts` 从建库起 0 行（写入路径一直走的是 practice_attempts），但它是
    题库的真正归属：`item_id` 外键指向 `quiz_items.id`。F12 把判分落库切到这里，
    所以按客户端隔离、错因标注、来源字节这几列必须补上 —— SQLite 改不了
    「NOT NULL 之外还缺列且想换类型」，只能重建；旧行原样搬过去。
    """
    columns = _column_names(connection, "attempts")
    if not columns or "client_id" in columns:
        return

    legacy_rows = connection.execute(
        """
        SELECT user_id, item_id, submitted, is_correct,
               first_diff_round, first_diff_step, first_diff_byte
        FROM attempts
        """
    ).fetchall()

    connection.execute("ALTER TABLE attempts RENAME TO attempts_v2")
    connection.execute(
        """
        CREATE TABLE attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            client_id TEXT NOT NULL DEFAULT 'legacy-default',
            item_id INTEGER NOT NULL REFERENCES quiz_items(id),
            submitted TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            first_diff_round INTEGER,
            first_diff_step TEXT,
            first_diff_step_index INTEGER,
            first_diff_byte INTEGER,
            source_bytes TEXT,
            design_tag TEXT,
            misconception TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for row in legacy_rows:
        connection.execute(
            """
            INSERT INTO attempts
                (user_id, client_id, item_id, submitted, is_correct,
                 first_diff_round, first_diff_step, first_diff_byte)
            VALUES (?, 'legacy-default', ?, ?, ?, ?, ?, ?)
            """,
            (
                row["user_id"],
                row["item_id"],
                row["submitted"],
                row["is_correct"],
                row["first_diff_round"],
                str(row["first_diff_step"]),
                row["first_diff_byte"],
            ),
        )
    connection.execute("DROP TABLE attempts_v2")
    logger.info("attempts rebuilt rows_kept=%s", len(legacy_rows))


def _rebuild_step_events(connection: sqlite3.Connection) -> None:
    """把 step_events 从「挂在会话上」改成「挂在客户端上」。

    原表 `session_id INTEGER NOT NULL REFERENCES sessions(id)`，而 `sessions`
    一行都没有（没有登录），所以它和之前的 tutor_logs 一样，从建库起就写不进去。
    现在按 `client_id` 记：谁在看第几步、停留多久，不需要先有账号。
    """
    columns = _column_names(connection, "step_events")
    if not columns or "session_id" not in columns:
        return

    legacy_rows = connection.execute(
        "SELECT step_index, event_type, dwell_ms, created_at FROM step_events"
    ).fetchall()

    connection.execute("ALTER TABLE step_events RENAME TO step_events_v2")
    connection.execute(
        """
        CREATE TABLE step_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL DEFAULT 'legacy-default',
            event_type TEXT NOT NULL,
            step_index INTEGER,
            dwell_ms INTEGER NOT NULL DEFAULT 0,
            at INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for row in legacy_rows:
        connection.execute(
            """
            INSERT INTO step_events
                (client_id, event_type, step_index, dwell_ms, created_at)
            VALUES ('legacy-default', ?, ?, ?, ?)
            """,
            (
                row["event_type"],
                row["step_index"],
                row["dwell_ms"],
                row["created_at"],
            ),
        )
    connection.execute("DROP TABLE step_events_v2")
    logger.info("step_events rebuilt rows_kept=%s", len(legacy_rows))


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
        if version < 1:
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

        step = "tutor_logs"
        if version < 2:
            _rebuild_tutor_logs(connection)

        step = "v3"
        if version < 3:
            _add_columns(
                connection,
                "quiz_items",
                (
                    ("item_code", "TEXT"),
                    ("plaintext_hex", "TEXT"),
                    ("key_hex", "TEXT"),
                    ("key_bits", "INTEGER"),
                ),
            )
            _rebuild_attempts(connection)
            _rebuild_step_events(connection)

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