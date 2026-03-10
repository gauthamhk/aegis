from src.storage.database import get_db
from src.utils.logging import get_logger

logger = get_logger(__name__)

MIGRATIONS = [
    {
        "version": 1,
        "description": "Initial schema — evaluations, drift_events, metrics_log",
        "sql": """
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
        """,
    },
    {
        "version": 2,
        "description": "Add request_id and domain indexes for faster lookups",
        "sql": """
            CREATE INDEX IF NOT EXISTS idx_evaluations_request_id ON evaluations(request_id);
            CREATE INDEX IF NOT EXISTS idx_evaluations_domain ON evaluations(domain);
            CREATE INDEX IF NOT EXISTS idx_metrics_log_timestamp ON metrics_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_metrics_log_name ON metrics_log(metric_name);
        """,
    },
]


async def run_migrations() -> None:
    db = await get_db()
    try:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "  version INTEGER PRIMARY KEY,"
            "  description TEXT,"
            "  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        cursor = await db.execute("SELECT MAX(version) FROM schema_version")
        row = await cursor.fetchone()
        current = row[0] if row[0] else 0

        for migration in MIGRATIONS:
            if migration["version"] > current:
                logger.info(
                    "migration.applying",
                    version=migration["version"],
                    description=migration["description"],
                )
                await db.executescript(migration["sql"])
                await db.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (migration["version"], migration["description"]),
                )
                await db.commit()
                logger.info("migration.applied", version=migration["version"])

        logger.info("migrations.complete", current_version=max(m["version"] for m in MIGRATIONS))
    finally:
        await db.close()
