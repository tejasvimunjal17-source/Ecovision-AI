# EcoVision AI — Supabase/Streamlit Cloud Upgrade Guide

## What changed

- Public landing page has no default Streamlit sidebar/navigation.
- Landing page now offers **Continue with Google** and **Continue with Email**.
- After login, a role-aware sidebar appears:
  - Citizen → Citizen Dashboard/tools
  - Officer → Officer Dashboard/tools
  - Admin → separate Admin Panel + officer/admin tools
- Streamlit's generated multipage list is hidden, so `app` does not appear as an unwanted sidebar item.
- Prakriti AI Connect is now a floating bottom-right widget on the public/authenticated UI. The original English/Hindi prompts and backend are preserved.
- Application persistence moved from local SQLite to **Supabase PostgreSQL**.
- The SQL-oriented business layer is retained through a locked-down Supabase RPC so existing complaint/reward/chat/report logic is not needlessly rewritten.
- OpenRouter remains the AI provider; the existing vision fallback logic is preserved.
- No API keys are hardcoded into source code.

## 1. Supabase setup

1. Create/open your Supabase project.
2. Open **SQL Editor → New query**.
3. Paste the complete contents of `database/schema.sql`.
4. Run it once.
5. In Supabase project settings, copy:
   - Project URL
   - service-role key (server-side secret only)

The service-role key must never be placed in frontend HTML, JavaScript, a public GitHub file, or a client-side application.

## 2. Streamlit Cloud Secrets

Add these to **Streamlit Cloud → Settings → Secrets**:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"

OPENROUTER_API_KEY = "YOUR_OPENROUTER_KEY"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_CHAT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_VISION_MODEL = "openrouter/free"
OPENROUTER_SITE_URL = "https://YOUR-APP.streamlit.app"
OPENROUTER_APP_NAME = "EcoVision AI"

APP_SECRET_KEY = "GENERATE_A_LONG_RANDOM_VALUE"
MUNICIPALITY_NAME = "Municipal Corporation of Gurugram (MCG)"
SUPPORT_EMAIL = "support@ecovision-ai.example.in"
SUPPORT_PHONE = "+91-9999999999"
```

## 3. Optional Google sign-in

The Google button is wired to Streamlit OIDC. To enable it, configure a Google OAuth Web Application and add the Streamlit callback URL:

`https://YOUR-APP.streamlit.app/oauth2callback`

Then add this to Streamlit Secrets:

```toml
[auth]
redirect_uri = "https://YOUR-APP.streamlit.app/oauth2callback"
cookie_secret = "YOUR_LONG_RANDOM_COOKIE_SECRET"
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_GOOGLE_OAUTH_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

If Google OIDC is not configured yet, **Continue with Email** continues to work.

## 4. Important deployment note

Do not depend on `database/ecovision.db` on Streamlit Cloud. The upgraded project intentionally does not use a local SQLite database for application persistence.

For complaint photos/videos, the current code continues to preserve the existing media path behavior. For a production-grade deployment, create a private Supabase Storage bucket such as `ecovision-media` and migrate media uploads there; the SQL complaint row should store the Storage object path/URL.

## 5. Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

For local development you may use `.env` with the same `SUPABASE_*` and `OPENROUTER_*` values. Never commit `.env`.

## 6. First login

The development seed in `database/db.py` creates:

- Email: `admin@ecovision.local`
- Password: `Admin@12345`

Change/remove this development account before production use. Better: create a production admin through your own controlled admin provisioning process.

## Architecture

```text
                     ┌─────────────────────────┐
                     │   EcoVision AI Landing   │
                     │  Google │ Email │ Guest  │
                     └────────────┬────────────┘
                                  │ login
              ┌───────────────────┴───────────────────┐
              │                                       │
       ┌──────▼──────┐                         ┌──────▼──────┐
       │ Citizen UI  │                         │ Admin Panel │
       │ role-based  │                         │ role-based  │
       └──────┬──────┘                         └──────┬──────┘
              │                                       │
              └──────────────┬────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │ Supabase Postgres │
                   │ users             │
                   │ complaints        │
                   │ rewards           │
                   │ chat_history      │
                   │ carbon_records    │
                   │ analytics data    │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │ OpenRouter / AI    │
                   │ Prakriti + Vision │
                   └───────────────────┘
```
