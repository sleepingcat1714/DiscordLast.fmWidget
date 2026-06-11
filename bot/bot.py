import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="67sigmaphonkrizz", intents=intents)
widget_group = app_commands.Group(name="lfwidget", description="Last.fm Widget commands")
app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)(widget_group)
app_commands.allowed_installs(guilds=True, users=True)(widget_group)


@bot.event
async def on_ready():
    from core.database import init_db
    init_db()
    await bot.tree.sync()
    print(f"Ready: {bot.user} ({bot.user.id})", flush=True)


def _error_view(title: str, description: str) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay(f"## {title}\n{description}")
    ))
    return view


@widget_group.command(name="setup", description="Link your Last.fm account to your Discord widget")
async def widget_setup(interaction: discord.Interaction):
    app_id = os.getenv("DISCORD_CLIENT_ID")
    api_key = os.getenv("LASTFM_API_KEY")
    domain = os.getenv("DOMAIN")
    discord_id = str(interaction.user.id)

    discord_auth_url = (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={app_id}"
        f"&response_type=token"
        f"&scope=openid+sdk.social_layer"
        f"&redirect_uri={domain}/callback/discord"
        f"&state={discord_id}"
    )

    from core.auth_token import generate as make_token
    signed = make_token(discord_id)
    callback_url = f"{domain}/callback/lastfm/{signed}"
    lastfm_auth_url = f"https://www.last.fm/api/auth/?api_key={api_key}&cb={callback_url}"

    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay(
            "## Last.fm Widget Setup\n"
            "Click both buttons below **in order**.\n\n"
            "**Step 1** — Grant Discord permission to show the widget\n"
            "**Step 2** — Connect your Last.fm account"
        ),
        discord.ui.Separator(visible=False),
        discord.ui.ActionRow(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="1. Authorize Discord",
                url=discord_auth_url,
            ),
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="2. Connect Last.fm",
                url=lastfm_auth_url,
            )
        ),
        discord.ui.Separator(visible=False),
        discord.ui.TextDisplay("-# Your widget will sync automatically after step 2.")
    ))

    await interaction.response.send_message(view=view, ephemeral=True)


@widget_group.command(name="refresh", description="Refresh your Last.fm widget stats")
async def widget_refresh(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    from core.database import get_user
    user = get_user(str(interaction.user.id))

    if not user:
        await interaction.followup.send(
            view=_error_view("Not Set Up", "Run `/lfwidget setup` first."),
            ephemeral=True
        )
        return

    try:
        from api.lastfm_api import get_lastfm_stats
        from api.widget_api import sync_widget
        stats = await get_lastfm_stats(user["lastfm_username"])
        custom_avatar = user.get("custom_avatar")

        await sync_widget(str(interaction.user.id), stats, custom_avatar=custom_avatar, identity_id=user.get("identity_id"))

        thumb = custom_avatar or stats["avatar"]
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"## Widget Refreshed\n"
                    f"**{stats['display_name']}** ({stats['username']})\n"
                    f"-# {stats['scrobbles']:,} scrobbles · {stats['artists']:,} artists"
                ),
                accessory=discord.ui.Thumbnail(thumb)
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                f"**Loved** `{stats['loved_tracks']:,}` · "
                f"**Tracks** `{stats['tracks']:,}` · "
                f"**Albums** `{stats['albums']:,}` · "
                f"**Daily Avg** `{stats['daily_average']}`"
            )
        ))

        await interaction.followup.send(view=view, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(
            view=_error_view("Refresh Failed", str(e)),
            ephemeral=True
        )


@widget_group.command(name="guide", description="How to display your widget on your Discord profile")
async def widget_guide(interaction: discord.Interaction):
    app_id = os.getenv("DISCORD_CLIENT_ID")

    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay("## How to Show Your Widget on Your Profile"),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Step 1 — Enable the experiment**\n"
            "In Vencord go to **Settings → Plugins**, enable the **Experiments** plugin.\n"
            "Then go to **Settings → Experiments**, search for:\n"
            "`2026-03-application-widget-v2-renderer`\n"
            "and set it to **Variant 1**."
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Step 2 — Add the widget to your profile**\n"
            "Open Discord's developer tools console and run:\n"
            "```js\n"
            "async function addWidget(appId) {\n"
            "    id = Vencord.Webpack.findByProps('getCurrentUser').getCurrentUser().id;\n"
            "    current_widgets = (await Vencord.Webpack.Common.RestAPI.get('/users/' + id + '/profile')).body.widgets\n"
            "    if (current_widgets.map(x=>x.data?.application_id).includes(appId)) {\n"
            "        return console.log('Already in your widgets');\n"
            "    }\n"
            "    current_widgets.unshift({'data':{'type':'application','application_id':appId}})\n"
            "    await Vencord.Webpack.Common.RestAPI.put({url:'/users/@me/widgets',body:{widgets:current_widgets}})\n"
            "}\n"
            f"addWidget(\"{app_id}\")\n"
            "```"
        ),
        discord.ui.Separator(visible=False),
        discord.ui.TextDisplay("-# Requires Vencord.")
    ))

    await interaction.response.send_message(view=view, ephemeral=True)


@widget_group.command(name="image", description="Set a custom image for your widget")
@app_commands.describe(url="Image URL", attachment="Or upload an image")
async def widget_image(interaction: discord.Interaction, url: str = None, attachment: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)

    from core.database import get_user, set_custom_avatar
    user = get_user(str(interaction.user.id))
    if not user:
        await interaction.followup.send(view=_error_view("Not Set Up", "Run `/lfwidget setup` first."), ephemeral=True)
        return

    image_url = url or (attachment.url if attachment else None)
    if not image_url:
        await interaction.followup.send(view=_error_view("No Image", "Provide a URL or upload an attachment."), ephemeral=True)
        return

    set_custom_avatar(str(interaction.user.id), image_url)

    try:
        from api.lastfm_api import get_lastfm_stats
        from api.widget_api import sync_widget
        stats = await get_lastfm_stats(user["lastfm_username"])
        await sync_widget(str(interaction.user.id), stats, custom_avatar=image_url, identity_id=user.get("identity_id"))
    except Exception as e:
        await interaction.followup.send(view=_error_view("Sync Failed", str(e)), ephemeral=True)
        return

    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay("## Custom Image Set\nYour widget image has been updated."),
            accessory=discord.ui.Thumbnail(image_url)
        )
    ))
    await interaction.followup.send(view=view, ephemeral=True)


@widget_group.command(name="imageremove", description="Remove custom image and use Last.fm avatar")
async def widget_imageremove(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    from core.database import get_user, set_custom_avatar
    user = get_user(str(interaction.user.id))
    if not user:
        await interaction.followup.send(view=_error_view("Not Set Up", "Run `/lfwidget setup` first."), ephemeral=True)
        return

    set_custom_avatar(str(interaction.user.id), None)

    try:
        from api.lastfm_api import get_lastfm_stats
        from api.widget_api import sync_widget
        stats = await get_lastfm_stats(user["lastfm_username"])
        await sync_widget(str(interaction.user.id), stats, custom_avatar=None, identity_id=user.get("identity_id"))
    except Exception as e:
        await interaction.followup.send(view=_error_view("Sync Failed", str(e)), ephemeral=True)
        return

    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay("## Custom Image Removed\nWidget is now using your Last.fm avatar.")
    ))
    await interaction.followup.send(view=view, ephemeral=True)


@widget_group.command(name="unlink", description="Unlink your Last.fm account")
async def widget_unlink(interaction: discord.Interaction):
    from core.database import delete_user
    delete_user(str(interaction.user.id))
    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.TextDisplay("## Unlinked\nYour Last.fm account has been removed from the bot."),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**To fully remove the widget:**\n"
            "Go to **Discord → User Settings → Authorized Apps** and revoke the Last.fm Widget app."
        )
    ))
    await interaction.response.send_message(view=view, ephemeral=True)


bot.tree.add_command(widget_group)
