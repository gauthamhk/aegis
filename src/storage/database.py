import aiosqlite
from pathlib import Path

from src.utils.config import settings

DB_PATH = Path(settings.database_url.replace("sqlite:///", ""))


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                timestamp REAL NOT NULL,
                prompt TEXT,
                response_text TEXT NOT NULL,
                context TEXT,
                domain TEXT DEFAULT 'general',
                faithfulness_score REAL,
                entropy_score REAL,
                citation_score REAL,
                composite_score REAL,
                action TEXT NOT NULL,
                explanation TEXT,
                layer_details TEXT,
                latency_ms REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS drift_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                z_score REAL,
                p_value REAL,
                window_mean REAL,
                baseline_mean REAL,
                severity TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS metrics_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                labels TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_evaluations_timestamp ON evaluations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_evaluations_action ON evaluations(action);
            CREATE INDEX IF NOT EXISTS idx_drift_events_timestamp ON drift_events(timestamp);
        """)
        await db.commit()
    finally:
        await db.close()
