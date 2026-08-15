"""
backend/auth.py — email/password authentication plus optional Google OIDC.

Email/password remains compatible with the original EcoVision flow.
Google sign-in uses Streamlit's server-side OIDC support and then mirrors the
identity into the same Supabase `users` table, so dashboards/complaints/rewards
use one application identity regardless of sign-in method.
"""
import os
import hashlib
import binascii
import re
import logging
import streamlit as st
from datetime import datetime, timedelta

from database.db import fetch_one, fetch_all, execute

logger = logging.getLogger("ecovision.auth")

PBKDF2_ITERATIONS = 260_000
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or binascii.hexlify(os.urandom(16)).decode()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return binascii.hexlify(dk).decode(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    check, _ = hash_password(password, salt)
    return bool(password_hash and salt and check == password_hash)


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must include at least one number."
    return True, ""


def register_user(full_name, email, phone, password, ward="", address="",
                  role="citizen", security_question="", security_answer=""):
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    ok, msg = validate_password_strength(password)
    if not ok:
        return False, msg
    if fetch_one("SELECT id FROM users WHERE email=?", (email,)):
        return False, "An account with this email already exists."

    pw_hash, salt = hash_password(password)
    ans_hash, _ = hash_password(security_answer.strip().lower(), salt) if security_answer else (None, salt)

    try:
        user_id = execute(
            """INSERT INTO users
               (full_name,email,phone,password_hash,salt,role,auth_provider,ward,address,
                security_question,security_answer_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?,?) RETURNING id""",
            (full_name.strip(), email, phone.strip(), pw_hash, salt, role, "email",
             ward, address, security_question, ans_hash),
        )
        _log_audit(user_id, "register", f"role={role}")
        return True, user_id
    except Exception as e:
        logger.exception("Registration failed")
        return False, f"Registration failed: {e}"


def _recent_failed_attempts(email: str) -> int:
    since = (datetime.utcnow() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    row = fetch_one(
        "SELECT COUNT(*) as c FROM login_attempts WHERE email=? AND success=FALSE AND created_at >= ?",
        (email, since),
    )
    return int(row["c"]) if row else 0


def login_user(email: str, password: str):
    email = email.strip().lower()

    if _recent_failed_attempts(email) >= MAX_FAILED_ATTEMPTS:
        return False, f"Too many failed attempts. Please try again in {LOCKOUT_WINDOW_MINUTES} minutes."

    user = fetch_one("SELECT * FROM users WHERE email=?", (email,))
    if not user or not user["is_active"]:
        execute("INSERT INTO login_attempts (email, success) VALUES (?,FALSE)", (email,))
        return False, "Invalid email or password."

    if not verify_password(password, user.get("password_hash"), user.get("salt")):
        execute("INSERT INTO login_attempts (email, success) VALUES (?,FALSE)", (email,))
        return False, "Invalid email or password."

    execute("INSERT INTO login_attempts (email, success) VALUES (?,TRUE)", (email,))
    execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user["id"],))
    _log_audit(user["id"], "login", "")
    user.pop("password_hash", None)
    user.pop("salt", None)
    user.pop("security_answer_hash", None)
    return True, user


def sync_google_user():
    """Sync the currently authenticated Streamlit OIDC user into Supabase."""
    try:
        identity = st.user  # imported lazily so backend remains import-safe
    except Exception as exc:
        raise RuntimeError("Google/OIDC is not configured in Streamlit Secrets.") from exc

    if not getattr(identity, "is_logged_in", False):
        return None

    email = (getattr(identity, "email", "") or "").strip().lower()
    if not email:
        raise RuntimeError("Google did not return an email address.")

    name = (getattr(identity, "name", "") or email.split("@")[0]).strip()
    subject = getattr(identity, "sub", None) or getattr(identity, "user_id", None)
    existing = fetch_one("SELECT * FROM users WHERE email=?", (email,))

    if existing:
        execute(
            "UPDATE users SET last_login=CURRENT_TIMESTAMP, auth_provider=?, auth_subject=? WHERE id=?",
            ("google", str(subject) if subject else None, existing["id"]),
        )
        existing["auth_provider"] = "google"
        existing.pop("password_hash", None)
        existing.pop("salt", None)
        existing.pop("security_answer_hash", None)
        return existing

    user_id = execute(
        """INSERT INTO users
           (full_name,email,password_hash,salt,role,auth_provider,auth_subject)
           VALUES (?,?,?,?,?,?,?) RETURNING id""",
        (name, email, None, None, "citizen", "google", str(subject) if subject else None),
    )
    user = fetch_one("SELECT * FROM users WHERE id=?", (user_id,))
    if user:
        user.pop("password_hash", None)
        user.pop("salt", None)
        user.pop("security_answer_hash", None)
        _log_audit(user_id, "google_register", "")
    return user


def get_security_question(email: str):
    user = fetch_one("SELECT security_question FROM users WHERE email=?", (email.strip().lower(),))
    return user["security_question"] if user else None


def reset_password(email: str, security_answer: str, new_password: str):
    email = email.strip().lower()
    user = fetch_one("SELECT * FROM users WHERE email=?", (email,))
    if not user:
        return False, "No account found with this email."
    if not user.get("security_answer_hash") or not user.get("salt"):
        return False, "This account uses Google sign-in. Continue with Google instead."

    ans_hash, _ = hash_password(security_answer.strip().lower(), user["salt"])
    if ans_hash != user["security_answer_hash"]:
        return False, "Security answer is incorrect."

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return False, msg

    pw_hash, salt = hash_password(new_password)
    execute("UPDATE users SET password_hash=?, salt=?, auth_provider='email' WHERE id=?",
            (pw_hash, salt, user["id"]))
    _log_audit(user["id"], "password_reset", "")
    return True, "Password reset successfully. You can now log in."


def _log_audit(user_id, action, details):
    try:
        execute("INSERT INTO audit_log (user_id, action, details) VALUES (?,?,?)",
                (user_id, action, details))
    except Exception:
        logger.warning("Audit log write failed", exc_info=True)
