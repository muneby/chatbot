import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'chatbot.db')
conn = sqlite3.connect(db_path)

# ── New tables ────────────────────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS bot_integrations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id       INTEGER UNIQUE REFERENCES bots(id),
    platform     TEXT    DEFAULT 'none',
    store_url    TEXT    DEFAULT '',
    api_key      TEXT    DEFAULT '',
    api_secret   TEXT    DEFAULT '',
    store_id     TEXT    DEFAULT '',
    last_synced  TEXT    DEFAULT '',
    synced_count INTEGER DEFAULT 0
)
""")
print("Ensured bot_integrations table.")

product_migrations = [
    ("source", "TEXT", "'manual'"),
]

bot_migrations = [
    ("primary_color",    "TEXT",    "'#008069'"),
    ("bot_persona_name", "TEXT",    "''"),
    ("is_demo",          "INTEGER", "0"),
    ("language",         "TEXT",    "'ar'"),
    ("avatar_emoji",     "TEXT",    "'🤖'"),
    ("currency",         "TEXT",    "'SAR'"),
    ("working_hours",    "TEXT",    "''"),
    ("fallback_message", "TEXT",    "''"),
    ("contact_info",     "TEXT",    "''"),
]

merchant_migrations = [
    ("business_name",   "TEXT", "''"),
    ("business_sector", "TEXT", "''"),
    ("country",         "TEXT", "''"),
    ("city",            "TEXT", "''"),
    ("phone",           "TEXT", "''"),
    ("email",           "TEXT", "''"),
    ("website",         "TEXT", "''"),
    ("employee_count",  "TEXT", "''"),
    ("bio",             "TEXT", "''"),
]

for col, col_type, default in product_migrations:
    try:
        conn.execute(f"ALTER TABLE products ADD COLUMN {col} {col_type} DEFAULT {default}")
        print(f"Added products.{col}")
    except Exception as e:
        print(f"Skipped products.{col}: {e}")

for col, col_type, default in bot_migrations:
    try:
        conn.execute(f"ALTER TABLE bots ADD COLUMN {col} {col_type} DEFAULT {default}")
        print(f"Added bots.{col}")
    except Exception as e:
        print(f"Skipped bots.{col}: {e}")

for col, col_type, default in merchant_migrations:
    try:
        conn.execute(f"ALTER TABLE merchants ADD COLUMN {col} {col_type} DEFAULT {default}")
        print(f"Added merchants.{col}")
    except Exception as e:
        print(f"Skipped merchants.{col}: {e}")

conn.commit()
conn.close()
print("Migration complete.")
