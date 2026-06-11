import hashlib
import hmac
import os
import secrets
import time

_TTL = 600  


def generate(discord_id: str) -> str:
    nonce = secrets.token_hex(32)
    expiry = int(time.time()) + _TTL
    payload = f"{discord_id}:{expiry}:{nonce}"
    secret = os.getenv("LASTFM_SECRET", "").encode()
    sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify(token: str) -> str | None:
    try:
        discord_id, expiry_str, nonce, sig = token.split(":", 3)
    except ValueError:
        return None

    if int(time.time()) > int(expiry_str):
        return None

    payload = f"{discord_id}:{expiry_str}:{nonce}"
    secret = os.getenv("LASTFM_SECRET", "").encode()
    expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, sig):
        return None

    return discord_id
