"""
app/migrate_db.py
================================================================================
SAFE DATABASE MIGRATION SCRIPT FOR HACKREC SHOWCASE
Inspects existing SQLite database tables, non-destructively updates columns
and nullability on engagement tables (upvotes, comments, status_changes),
and creates new Showcase tables without losing any existing data.
================================================================================
"""

from sqlalchemy import inspect, text
from app.models import db


def upgrade_schema(app=None):
    """
    Safely upgrades the database schema for the Showcase extension.
    Works with both active SQLite files and test in-memory databases.
    """
    with db.engine.connect() as conn:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # 0. Add user moderation columns if missing
        if "users" in existing_tables:
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            if "is_banned" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_banned BOOLEAN NOT NULL DEFAULT 0"))
                conn.commit()
            if "ban_reason" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN ban_reason VARCHAR(255)"))
                conn.commit()
            if "banned_at" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN banned_at DATETIME"))
                conn.commit()
            if "registration_no" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN registration_no VARCHAR(10)"))
                conn.commit()
                # Copy existing roll_no into registration_no if roll_no column exists
                if "roll_no" in user_cols:
                    conn.execute(text("UPDATE users SET registration_no = roll_no WHERE registration_no IS NULL AND roll_no IS NOT NULL"))
                    conn.commit()

        # 1. Add showcase_project_id if missing
        for tbl in ["upvotes", "comments", "status_changes"]:
            if tbl in existing_tables:
                columns = [c["name"] for c in inspector.get_columns(tbl)]
                if "showcase_project_id" not in columns:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN showcase_project_id INTEGER REFERENCES showcase_projects(id)"))
                    conn.commit()

        # Re-inspect to check submission_id nullability
        inspector = inspect(db.engine)

        # 2. Check if submission_id is NOT NULL in upvotes (SQLite requires table recreation to alter NOT NULL)
        if "upvotes" in existing_tables:
            col_info = {c["name"]: c for c in inspector.get_columns("upvotes")}
            if col_info.get("submission_id", {}).get("nullable") is False:
                conn.execute(text("PRAGMA foreign_keys=OFF;"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS upvotes_new (
                        id INTEGER PRIMARY KEY,
                        submission_id INTEGER REFERENCES submissions(id),
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        created_at DATETIME,
                        showcase_project_id INTEGER REFERENCES showcase_projects(id)
                    );
                """))
                conn.execute(text("""
                    INSERT INTO upvotes_new (id, submission_id, user_id, created_at, showcase_project_id)
                    SELECT id, submission_id, user_id, created_at, showcase_project_id FROM upvotes;
                """))
                conn.execute(text("DROP TABLE upvotes;"))
                conn.execute(text("ALTER TABLE upvotes_new RENAME TO upvotes;"))
                conn.execute(text("PRAGMA foreign_keys=ON;"))
                conn.commit()

        # 3. Check comments table nullability
        if "comments" in existing_tables:
            col_info = {c["name"]: c for c in inspector.get_columns("comments")}
            if col_info.get("submission_id", {}).get("nullable") is False:
                conn.execute(text("PRAGMA foreign_keys=OFF;"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS comments_new (
                        id INTEGER PRIMARY KEY,
                        submission_id INTEGER REFERENCES submissions(id),
                        author_id INTEGER NOT NULL REFERENCES users(id),
                        body TEXT NOT NULL,
                        created_at DATETIME,
                        is_deleted BOOLEAN NOT NULL DEFAULT 0,
                        showcase_project_id INTEGER REFERENCES showcase_projects(id)
                    );
                """))
                conn.execute(text("""
                    INSERT INTO comments_new (id, submission_id, author_id, body, created_at, is_deleted, showcase_project_id)
                    SELECT id, submission_id, author_id, body, created_at, is_deleted, showcase_project_id FROM comments;
                """))
                conn.execute(text("DROP TABLE comments;"))
                conn.execute(text("ALTER TABLE comments_new RENAME TO comments;"))
                conn.execute(text("PRAGMA foreign_keys=ON;"))
                conn.commit()

        # 4. Check status_changes table nullability
        if "status_changes" in existing_tables:
            col_info = {c["name"]: c for c in inspector.get_columns("status_changes")}
            if col_info.get("submission_id", {}).get("nullable") is False:
                conn.execute(text("PRAGMA foreign_keys=OFF;"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS status_changes_new (
                        id INTEGER PRIMARY KEY,
                        submission_id INTEGER REFERENCES submissions(id),
                        actor_id INTEGER NOT NULL REFERENCES users(id),
                        from_status VARCHAR(50) NOT NULL,
                        to_status VARCHAR(50) NOT NULL,
                        public_comment TEXT,
                        internal_note TEXT,
                        created_at DATETIME,
                        showcase_project_id INTEGER REFERENCES showcase_projects(id)
                    );
                """))
                conn.execute(text("""
                    INSERT INTO status_changes_new (id, submission_id, actor_id, from_status, to_status, public_comment, internal_note, created_at, showcase_project_id)
                    SELECT id, submission_id, actor_id, from_status, to_status, public_comment, internal_note, created_at, showcase_project_id FROM status_changes;
                """))
                conn.execute(text("DROP TABLE status_changes;"))
                conn.execute(text("ALTER TABLE status_changes_new RENAME TO status_changes;"))
                conn.execute(text("PRAGMA foreign_keys=ON;"))
                conn.commit()

    # 5. Create any newly added tables
    db.create_all()
