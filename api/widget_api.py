import aiohttp
import os

async def sync_widget(discord_id: str, stats: dict, custom_avatar: str | None = None, identity_id: str = None):
    app_id = os.getenv("DISCORD_CLIENT_ID")
    bot_token = os.getenv("DISCORD_TOKEN")
    headers = {"Authorization": f"Bot {bot_token}"}

    payload = {
        "username": stats["username"],
        "data": {
            "dynamic": [
                {"type": 1, "name": "display_name",  "value": stats["display_name"]},
                {"type": 1, "name": "username",       "value": stats["username"]},
                {"type": 1, "name": "listening_since","value": stats["listening_since"]},
                {"type": 3, "name": "avatar",         "value": {"url": custom_avatar or stats["avatar"]}},
                {"type": 3, "name": "mini_avatar",    "value": {"url": stats["avatar"]}},
                {"type": 2, "name": "scrobbles",      "value": stats["scrobbles"]},
                {"type": 1, "name": "scrobbles_text", "value": stats["scrobbles_text"]},
                {"type": 2, "name": "loved_tracks",   "value": stats["loved_tracks"]},
                {"type": 2, "name": "daily_average",  "value": stats["daily_average"]},
                {"type": 2, "name": "tracks",         "value": stats["tracks"]},
                {"type": 2, "name": "albums",         "value": stats["albums"]},
                {"type": 2, "name": "artists",        "value": stats["artists"]},
            ]
        }
    }

    base = f"https://discord.com/api/v9/applications/{app_id}/users/{discord_id}/identities"
    external_id = identity_id or stats["username"].lstrip("@")

    async with aiohttp.ClientSession() as session:
        async with session.patch(f"{base}/{external_id}/profile", json=payload, headers=headers) as resp:
            if not resp.ok:
                data = await resp.json()
                code = data.get("code")
                if code == 50035:
                    raise Exception(
                        "Your widget slot needs to be recreated. Please run `/lfwidget setup` again and complete both steps."
                    )
                elif code == 40106:
                    raise Exception(
                        "This Last.fm account is already linked to a different Discord account. "
                        "You may need to disconnect it from another widget first."
                    )
                else:
                    raise Exception(f"Discord API error {resp.status}: {data}")
