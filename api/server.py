import asyncio
import hashlib
import html
import os
import re
import aiohttp

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_DISCORD_ID_RE = re.compile(r"^\d{17,20}$")


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p>{body}</p>
</body>
</html>"""


def _lastfm_sig(params: dict) -> str:
    secret = os.getenv("LASTFM_SECRET")
    base = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    return hashlib.md5((base + secret).encode()).hexdigest()


@app.get("/")
@limiter.limit("30/minute")
async def index(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="https://assumi.ng", status_code=301)


@app.get("/callback/discord", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def discord_callback(request: Request):
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Last.fm Widget</title>
</head>
<body>
<h1 id="title">Authorizing...</h1>
<p id="body">Please wait.</p>
<script>
const hash = window.location.hash.substring(1);
const params = new URLSearchParams(hash);
const token = params.get('access_token');
const state = params.get('state');
if (token && state) {{
    fetch('/callback/discord/token', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{token, state}})
    }})
    .then(r => r.ok ? r.json() : Promise.reject(r))
    .then(() => {{
        document.getElementById('title').textContent = 'Authorized';
        document.getElementById('body').textContent = 'Discord permission granted. You can close this tab.';
    }})
    .catch(() => {{
        document.getElementById('title').textContent = 'Something went wrong';
        document.getElementById('body').innerHTML = 'Please try <strong>/lfwidget setup</strong> again.';
    }});
}} else {{
    document.getElementById('title').textContent = 'Something went wrong';
    document.getElementById('body').innerHTML = 'No token found. Please try <strong>/lfwidget setup</strong> again.';
}}
</script>
</body>
</html>"""
    return HTMLResponse(page)


@app.post("/callback/discord/token")
@limiter.limit("10/minute")
async def discord_token(request: Request, payload: dict):
    token = payload.get("token", "")
    state = payload.get("state", "")

    if not token or not state or not _DISCORD_ID_RE.match(state):
        from fastapi.responses import JSONResponse
        return JSONResponse({"ok": False, "error": "invalid payload"}, status_code=400)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {token}"}
        ) as resp:
            if not resp.ok:
                from fastapi.responses import JSONResponse
                return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)
            user_data = await resp.json()

    if str(user_data.get("id")) != state:
        from fastapi.responses import JSONResponse
        return JSONResponse({"ok": False, "error": "token/state mismatch"}, status_code=403)

    return {"ok": True}


@app.get("/callback/lastfm/{signed_token}", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def lastfm_callback(request: Request, signed_token: str, token: str):
    from core.auth_token import verify
    discord_id = verify(signed_token)
    if not discord_id:
        return HTMLResponse(
            _page("Link Expired", "This setup link has expired or is invalid. Please run <strong>/lfwidget setup</strong> again."),
            status_code=400
        )

    api_key = os.getenv("LASTFM_API_KEY")

    params = {
        "method": "auth.getSession",
        "api_key": api_key,
        "token": token,
    }
    sig = _lastfm_sig(params)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={**params, "api_sig": sig, "format": "json"}
        ) as resp:
            data = await resp.json()

    if "error" in data:
        return HTMLResponse(
            _page("Authorization Failed",
                  f"{html.escape(data.get('message', 'Unknown error'))}<br>"
                  "Please try <strong>/lfwidget setup</strong> again."),
            status_code=400
        )

    session_key = data["session"]["key"]
    username = data["session"]["name"]

    from core.database import save_user
    save_user(discord_id, username, session_key)

    asyncio.create_task(_auto_sync(discord_id, username))

    return HTMLResponse(
        _page("Last.fm Connected",
              f"Linked as <strong>{html.escape(username)}</strong>. Your widget is syncing — you can close this tab.")
    )


async def _auto_sync(discord_id: str, username: str):
    try:
        from api.lastfm_api import get_lastfm_stats
        from api.widget_api import sync_widget
        from core.database import get_user
        stats = await get_lastfm_stats(username)
        user = get_user(discord_id)
        identity_id = user.get("identity_id") if user else discord_id
        await sync_widget(discord_id, stats, identity_id=identity_id)
    except Exception:
        pass
