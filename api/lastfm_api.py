import asyncio
import os
from datetime import datetime
import aiohttp

BASE = "https://ws.audioscrobbler.com/2.0/"

def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n/1_000:.1f}K".rstrip("0").rstrip(".")
    return str(n)

async def get_lastfm_stats(username: str) -> dict:
    api_key = os.getenv("LASTFM_API_KEY")

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE, params={
            "method": "user.getinfo",
            "user": username,
            "api_key": api_key,
            "format": "json"
        }) as resp:
            data = await resp.json()

        if "error" in data:
            raise Exception(f"Last.fm user not found: `{username}`")

        user = data["user"]

        loved_resp, friends_resp = await asyncio.gather(
            session.get(BASE, params={
                "method": "user.getlovedtracks",
                "user": username,
                "api_key": api_key,
                "format": "json",
                "limit": 1
            }),
            session.get(BASE, params={
                "method": "user.getfriends",
                "user": username,
                "api_key": api_key,
                "format": "json",
                "limit": 1
            })
        )
        async with loved_resp:
            loved_data = await loved_resp.json()
        async with friends_resp:
            friends_data = await friends_resp.json()

        loved_tracks = int(loved_data.get("lovedtracks", {}).get("@attr", {}).get("total", 0))
        friends = 0 if "error" in friends_data else int(friends_data.get("friends", {}).get("@attr", {}).get("total", 0))

    images = user.get("image", [])
    avatar = ""
    for img in reversed(images):
        if img.get("#text"):
            avatar = img["#text"]
            break

    display_name = user.get("realname") or user.get("name", username)
    scrobbles = int(user.get("playcount", 0))

    registered_ts = user.get("registered", {}).get("unixtime") or user.get("registered", {}).get("#text")
    if registered_ts:
        listening_since = f"Scrobbling Since {datetime.utcfromtimestamp(int(registered_ts)).strftime('%B %Y')}"
        days = max((datetime.utcnow() - datetime.utcfromtimestamp(int(registered_ts))).days, 1)
        daily_average = round(scrobbles / days)
    else:
        listening_since = ""
        daily_average = 0

    return {
        "display_name": display_name,
        "username": f"@{user['name']}",
        "listening_since": listening_since,
        "daily_average": daily_average,
        "avatar": avatar,
        "scrobbles": scrobbles,
        "scrobbles_text": f"{_fmt(scrobbles)} Scrobbles",
        "loved_tracks": loved_tracks,
        "friends": friends,
        "tracks": int(user.get("track_count", 0)),
        "albums": int(user.get("album_count", 0)),
        "artists": int(user.get("artist_count", 0)),
    }
