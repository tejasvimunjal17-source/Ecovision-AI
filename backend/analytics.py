"""PostgreSQL analytics queries for EcoVision AI."""
from database.db import fetch_all, fetch_one


def kpi_summary():
    total = int(fetch_one("SELECT COUNT(*) c FROM complaints")["c"])
    resolved = int(fetch_one("SELECT COUNT(*) c FROM complaints WHERE status='Resolved'")["c"])
    pending = int(fetch_one("SELECT COUNT(*) c FROM complaints WHERE status NOT IN ('Resolved','Rejected')")["c"])
    citizens = int(fetch_one("SELECT COUNT(*) c FROM users WHERE role='citizen'")["c"])
    high_priority_open = int(fetch_one(
        "SELECT COUNT(*) c FROM complaints WHERE priority='High' AND status NOT IN ('Resolved','Rejected')"
    )["c"])
    avg_row = fetch_one(
        """SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600),0) AS h
           FROM complaints WHERE resolved_at IS NOT NULL"""
    )
    avg_resolution_hours = float(avg_row["h"] or 0)
    return {
        "total_complaints": total,
        "resolved": resolved,
        "pending": pending,
        "resolution_rate": round((resolved / total * 100), 1) if total else 0,
        "citizens": citizens,
        "high_priority_open": high_priority_open,
        "avg_resolution_hours": round(avg_resolution_hours, 1),
    }


def complaints_by_category():
    return fetch_all("SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC")


def complaints_by_status():
    return fetch_all("SELECT status, COUNT(*) as count FROM complaints GROUP BY status")


def complaints_by_priority():
    return fetch_all("SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority")


def complaints_by_ward():
    return fetch_all(
        "SELECT ward, COUNT(*) as count FROM complaints WHERE ward IS NOT NULL AND ward!='' "
        "GROUP BY ward ORDER BY count DESC"
    )


def complaints_daily_trend(days=30):
    return fetch_all(
        """SELECT created_at::date AS day, COUNT(*) AS count
           FROM complaints
           WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day' * ?
           GROUP BY created_at::date ORDER BY day""",
        (int(days),),
    )


def complaints_monthly_trend():
    return fetch_all(
        """SELECT to_char(created_at, 'YYYY-MM') AS month, COUNT(*) AS count
           FROM complaints GROUP BY to_char(created_at, 'YYYY-MM') ORDER BY month"""
    )


def officer_performance():
    return fetch_all(
        """SELECT u.full_name AS officer,
                  COUNT(c.id) AS assigned,
                  COALESCE(SUM(CASE WHEN c.status='Resolved' THEN 1 ELSE 0 END),0) AS resolved
           FROM users u LEFT JOIN complaints c ON c.assigned_officer_id=u.id
           WHERE u.role='officer'
           GROUP BY u.id, u.full_name
           ORDER BY assigned DESC"""
    )
