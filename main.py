import asyncio
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from bot.bot import bot
from api.server import app


async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 7396)), log_level="warning")
    server = uvicorn.Server(config)

    await asyncio.gather(
        bot.start(os.getenv("DISCORD_TOKEN")),
        server.serve()
    )


if __name__ == "__main__":
    asyncio.run(main())
