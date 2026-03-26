#!/usr/bin/env python3
"""
Migrate outdoor sessions and saved options from the old
kids_outdoor_tracker SQLite database to the Home Hub PostgreSQL database.

Usage:
    python scripts/migrate_outdoor.py [path_to_sqlite_db]

Default SQLite path: /Users/qbot/Projects/kids_outdoor_tracker/data/outside.db
"""

import asyncio
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.database import async_session, engine


SQLITE_PATH = "/Users/qbot/Projects/kids_outdoor_tracker/data/outside.db"


async def migrate(sqlite_path: str):
    """Migrate outdoor data from SQLite to PostgreSQL."""
    # Connect to SQLite
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Read sessions
    cursor.execute("SELECT * FROM sessions ORDER BY id")
    sessions = [dict(row) for row in cursor.fetchall()]

    # Read saved options
    cursor.execute("SELECT * FROM saved_options ORDER BY id")
    options = [dict(row) for row in cursor.fetchall()]

    conn.close()

    print(f"Found {len(sessions)} sessions and {len(options)} saved options to migrate")

    if not sessions and not options:
        print("Nothing to migrate!")
        return

    def parse_date(s):
        """Convert 'YYYY-MM-DD' string to date object."""
        if not s:
            return None
        return datetime.strptime(s, "%Y-%m-%d").date()

    def parse_datetime(s):
        """Convert datetime string to datetime object."""
        if not s:
            return datetime.utcnow()
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.fromisoformat(s)

    async with async_session() as db:
        # Migrate sessions
        migrated_sessions = 0
        for s in sessions:
            session_date = parse_date(s["date"])
            # Check if already exists (by date + start_time + location)
            result = await db.execute(
                text("""
                    SELECT id FROM outdoor_sessions
                    WHERE session_date = :date AND start_time = :start AND location = :location
                """),
                {"date": session_date, "start": s["start_time"], "location": s["location"]},
            )
            if result.fetchone():
                print(f"  Skipping session {s['date']} {s['start_time']} at {s['location']} (already exists)")
                continue

            await db.execute(
                text("""
                    INSERT INTO outdoor_sessions
                    (session_date, start_time, end_time, duration_minutes, location, activity,
                     weather, notes, source, created_by, created_at)
                    VALUES (:date, :start_time, :end_time, :duration, :location, :activity,
                            :weather, :notes, :source, :created_by, :created_at)
                """),
                {
                    "date": session_date,
                    "start_time": s["start_time"],
                    "end_time": s["end_time"],
                    "duration": s["duration_minutes"],
                    "location": s["location"],
                    "activity": s["activity"],
                    "weather": s["weather"],
                    "notes": s["notes"],
                    "source": s["source"] or "migrated",
                    "created_by": s["created_by"] or "dj",
                    "created_at": parse_datetime(s["created_at"]),
                },
            )
            migrated_sessions += 1

        # Migrate saved options
        migrated_options = 0
        for o in options:
            # Use upsert: if field+value exists, update use_count to max
            result = await db.execute(
                text("""
                    SELECT id, use_count FROM saved_options
                    WHERE field = :field AND value = :value
                """),
                {"field": o["field"], "value": o["value"]},
            )
            existing = result.fetchone()
            if existing:
                # Update use_count if the migrated count is higher
                if o["use_count"] > existing[1]:
                    await db.execute(
                        text("UPDATE saved_options SET use_count = :count WHERE id = :id"),
                        {"count": o["use_count"], "id": existing[0]},
                    )
                    print(f"  Updated option {o['field']}={o['value']} use_count to {o['use_count']}")
                else:
                    print(f"  Skipping option {o['field']}={o['value']} (already exists)")
                continue

            await db.execute(
                text("""
                    INSERT INTO saved_options (field, value, use_count, last_used)
                    VALUES (:field, :value, :use_count, :last_used)
                """),
                {
                    "field": o["field"],
                    "value": o["value"],
                    "use_count": o["use_count"],
                    "last_used": parse_datetime(o["last_used"]),
                },
            )
            migrated_options += 1

        await db.commit()

    print(f"\nMigration complete!")
    print(f"  Sessions migrated: {migrated_sessions} (skipped: {len(sessions) - migrated_sessions})")
    print(f"  Options migrated: {migrated_options} (skipped: {len(options) - migrated_options})")

    # Clean up engine
    await engine.dispose()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else SQLITE_PATH
    if not Path(path).exists():
        print(f"SQLite database not found at: {path}")
        sys.exit(1)

    print(f"Migrating from: {path}")
    asyncio.run(migrate(path))
