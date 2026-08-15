"""
database/db.py
----------------
Supabase-first persistence adapter for EcoVision AI.

The rest of the application can keep its existing small SQL-oriented API:
    fetch_all(query, params)
    fetch_one(query, params)
    execute(query, params)

Queries are executed through a locked-down PostgreSQL RPC function installed by
database/schema.sql. No local SQLite file is used in production or on
Streamlit Community Cloud.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from config import settings

logger = logging.getLogger("ecovision.db")

_client_cache = {}


class SupabaseUnavailableError(RuntimeError):
    pass


def _get_client():
    if "client" in _client_cache:
        return _client_cache["client"]
    if not settings.SUPABASE_CONFIG.is_configured:
        raise SupabaseUnavailableError(
            "Supabase is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "to Streamlit Cloud Secrets or your local .env."
        )
    try:
        from supabase import create_client
        _client_cache["client"] = create_client(
            settings.SUPABASE_CONFIG.url,
            settings.SUPABASE_CONFIG.service_role_key,
        )
        return _client_cache["client"]
    except Exception as exc:
        raise SupabaseUnavailableError(f"Could not connect to Supabase: {exc}") from exc


def is_supabase_configured() -> bool:
    return settings.SUPABASE_CONFIG.is_configured


def _sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    s = str(value)
    return "'" + s.replace("'", "''") + "'"


def _bind_sql(query: str, params: tuple | list = ()):
    """Safely bind the legacy '?' placeholders before sending SQL to RPC."""
    params = list(params or [])
    parts = query.split("?")
    if len(parts) == 1:
        sql = query
    else:
        if len(parts) - 1 != len(params):
            raise ValueError(
                f"SQL parameter mismatch: expected {len(parts)-1}, got {len(params)}"
            )
        sql = parts[0]
        for i, value in enumerate(params):
            sql += _sql_literal(value) + parts[i + 1]

    # SQLite -> PostgreSQL compatibility for the existing codebase.
    replacements = [
        (r"\bdatetime\(\s*'now'\s*\)", "CURRENT_TIMESTAMP"),
        (r"\bdate\(\s*created_at\s*\)", "created_at::date"),
        (r"\bis_active\s*=\s*1\b", "is_active = TRUE"),
        (r"\bis_active\s*=\s*0\b", "is_active = FALSE"),
        (r"\bsuccess\s*=\s*1\b", "success = TRUE"),
        (r"\bsuccess\s*=\s*0\b", "success = FALSE"),
        (r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO"),
    ]
    for pattern, repl in replacements:
        sql = re.sub(pattern, repl, sql, flags=re.IGNORECASE)

    # PostgreSQL needs ON CONFLICT for the one legacy INSERT OR IGNORE call.
    if "INSERT INTO categories" in sql.upper() and "ON CONFLICT" not in sql.upper():
        sql += " ON CONFLICT (name) DO NOTHING"

    return sql.strip().rstrip(";") + ";"


def _rpc(sql: str):
    client = _get_client()
    try:
        response = client.rpc("ecovision_query", {"p_sql": sql}).execute()
        return response.data
    except Exception as exc:
        logger.exception("Supabase RPC query failed")
        raise SupabaseUnavailableError(f"Supabase query failed: {exc}") from exc


def fetch_all(query: str, params: tuple = ()):
    sql = _bind_sql(query, params)
    data = _rpc(sql)
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    return list(data)


def fetch_one(query: str, params: tuple = ()):
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query: str, params: tuple = ()):
    """Execute DML. If the SQL has RETURNING, the returned row is exposed."""
    sql = _bind_sql(query, params)
    data = _rpc(sql)
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "id" in data[0]:
            return data[0]["id"]
        return None
    if isinstance(data, dict):
        if "id" in data:
            return data["id"]
        return data.get("rowcount")
    return None


def init_db():
    """Verify Supabase is reachable and seed safe defaults.

    Schema creation is intentionally NOT performed at runtime. Run
    database/schema.sql once in Supabase SQL Editor.
    """
    if not settings.SUPABASE_CONFIG.is_configured:
        logger.warning("Supabase is not configured yet.")
        return

    try:
        fetch_one("SELECT id FROM users LIMIT 1")
    except Exception:
        raise

    _seed_categories()
    _seed_recycling_centres()
    _seed_admin()


def _seed_categories():
    defaults = [
        ("Plastic", "Plastic bottles, bags, wrappers, containers", "🧴",
         "Rinse and place in the dry-waste bin; drop bulk plastic at an authorized recycler."),
        ("Organic", "Food scraps, garden waste, biodegradable matter", "🍂",
         "Compost at home or place in the wet-waste (green) bin for municipal composting."),
        ("Paper", "Newspaper, cardboard, cartons, office paper", "📄",
         "Flatten and keep dry; place in the dry-waste bin or sell to a kabadiwala."),
        ("Glass", "Bottles, jars, broken glassware", "🍾",
         "Wrap broken pieces safely, place in dry-waste bin marked 'glass'."),
        ("Metal", "Cans, foil, scrap metal, utensils", "🔩",
         "Place in dry-waste bin; scrap metal can be sold to authorized scrap dealers."),
        ("Mixed", "Non-segregated general waste", "🗑️",
         "Please segregate at source; mixed waste delays processing and recycling."),
        ("E-Waste", "Batteries, electronics, wires, appliances", "🔋",
         "Never mix with household waste — drop at an authorized MCG e-waste collection centre."),
        ("Biomedical", "Medical/clinical waste, sharps, PPE", "🩺",
         "Requires special handling — contact MCG health department or an authorized biomedical waste handler."),
        ("Construction", "Debris, rubble, bricks, concrete", "🧱",
         "Book a municipal C&D waste pickup; do not dump on roads or drains."),
    ]
    for row in defaults:
        execute(
            "INSERT INTO categories (name, description, icon, disposal_guide) "
            "VALUES (?,?,?,?) ON CONFLICT (name) DO NOTHING", row
        )


def _seed_recycling_centres():
    existing = fetch_one("SELECT id FROM recycling_centres LIMIT 1")
    if existing:
        return
    centres = [
        ("MCG Material Recovery Facility - Sector 39", "Dry Waste MRF", "Sector 39, Gurugram",
         "Sector 39", 28.4501, 77.0424, "+91-124-2222222", "Plastic,Paper,Metal,Glass"),
        ("MCG E-Waste Collection Centre - Sector 14", "E-Waste", "Sector 14, Gurugram",
         "Sector 14", 28.4699, 77.0266, "+91-124-2333333", "E-Waste,Batteries"),
        ("Composting Unit - Sector 52", "Organic/Composting", "Sector 52, Gurugram",
         "Sector 52", 28.4177, 77.0729, "+91-124-2444444", "Organic"),
        ("Scrap & Metal Recyclers - Udyog Vihar", "Scrap/Metal", "Udyog Vihar Phase 3, Gurugram",
         "Udyog Vihar", 28.5017, 77.0881, "+91-124-2555555", "Metal,Glass"),
    ]
    for row in centres:
        execute(
            """INSERT INTO recycling_centres
               (name, type, address, ward, latitude, longitude, contact, materials_accepted)
               VALUES (?,?,?,?,?,?,?,?)""",
            row,
        )


def _seed_admin():
    """Create a development admin only when no admin exists.

    Production administrators should be created/rotated through the Admin
    Panel rather than relying on this development seed.
    """
    existing = fetch_one("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if existing:
        return
    from backend.auth import hash_password
    pw_hash, salt = hash_password("Admin@12345")
    execute(
        """INSERT INTO users
           (full_name, email, phone, password_hash, salt, role, ward)
           VALUES (?,?,?,?,?,?,?)""",
        ("System Administrator", "admin@ecovision.local", "9999999999",
         pw_hash, salt, "admin", "HQ"),
    )
    logger.warning("Created development admin admin@ecovision.local — change credentials immediately.")
