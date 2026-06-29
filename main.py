import asyncio
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from bot.bot import bot
from api.server import app

REFRESH_INTERVAL = 5 * 60 * 60


async def _auto_refresh_loop():
    await asyncio.sleep(REFRESH_INTERVAL)
    while True:
        try:
            from core.database import get_all_users
            from api.lastfm_api import get_lastfm_stats
            from api.widget_api import sync_widget
            for user in get_all_users():
                try:
                    stats = await get_lastfm_stats(user["lastfm_username"])
                    await sync_widget(user["discord_id"], stats, custom_avatar=user.get("custom_avatar"), identity_id=user["identity_id"])
                except Exception:
                    pass
        except Exception:
            pass
        await asyncio.sleep(REFRESH_INTERVAL)


async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 7396)), log_level="warning")
    server = uvicorn.Server(config)

    asyncio.create_task(_auto_refresh_loop())

    await asyncio.gather(
        bot.start(os.getenv("DISCORD_TOKEN")),
        server.serve()
    )


if __name__ == "__main__":
    asyncio.run(main())
