# Last.fm Widget Bot

Displays your Last.fm stats as a widget on your Discord profile.


## What it shows

- Scrobbles, artists, loved tracks, albums, daily average
- Listening since date
- Last.fm avatar (or custom image)


## Note

Discord has unfortunately limited the ability for people to use widgets made by others. Only the owner of an application (or team members) can add it to their profile, so if you want to use this widget, you'll need to host your own instance with your own Discord application.

Also, as long as there are widgets not made by you on your widgets board, you won't be able to save or make changes to any widget on your profile.


## Commands

- `/lfwidget setup`  link your Last.fm account
- `/lfwidget refresh`  manually refresh stats (also auto-refreshes every 5 hours)
- `/lfwidget image`  set a custom widget image
- `/lfwidget imageremove`  revert to Last.fm avatar
- `/lfwidget guide`  how to show the widget on your profile
- `/lfwidget unlink`  unlink your account


## Setup

**1. Install**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create `.env`**

```env
DISCORD_TOKEN=
DISCORD_CLIENT_ID=
LASTFM_API_KEY=
LASTFM_SECRET=
DOMAIN=https://yourdomain.com
PORT=7824
```

No domain? Use your server's public IP and port instead:

```env
DOMAIN=http://IP:7824
```

**3. Discord app settings**

- Add `{DOMAIN}/callback/discord` as a redirect URI
- Enable User install
- Enable the Activities / Widget SDK feature

**4. Last.fm app settings**

- Create an app at [last.fm/api/accounts](https://www.last.fm/api/accounts)
- Set callback to `{DOMAIN}/callback/lastfm`

**5. Run**

```bash
python main.py
```


## Adding the widget to ur profile 

Requires [Vencord](https://vencord.dev).

1. Go to **Settings → Plugins**, enable the **Experiments** plugin
2. Go to **Settings → Experiments**, search for `2026-03-application-widget-v2-renderer` and set it to **Variant 1**
3. Run `/lfwidget guide` in Discord for instructions on adding the widget to your profile


## Setting up in the Discord Developer Portal

1. Create an application on the [Discord Developer Portal](https://discord.com/developers/applications)
2. Go to **Games → Social SDK** and submit the form (just lie) to get Social SDK access
3. Open the browser console on the Developer Portal and run:

```js
let _mods = webpackChunkdiscord_developers.push([[Symbol()],{},r=>r.c]);
webpackChunkdiscord_developers.pop();

let findByProps = (...props) => {
    for (let m of Object.values(_mods)) {
        try {
            if (!m.exports || m.exports === window) continue;
            if (props.every((x) => m.exports?.[x])) return m.exports;
            for (let ex in m.exports) {
                if (props.every((x) => m.exports?.[ex]?.[x]) && m.exports[ex][Symbol.toStringTag] !== 'IntlMessagesProxy') return m.exports[ex];
            }
        } catch {}
    }
}

findByProps("getAll").getAll().find(e=>e.getName() === "ApexExperimentStore").createOverride("2026-03-widget-config-editor", 1)
```

4. Click back and reopen your app (don't refresh). A **Widget** page will appear under Games where you can build your widget.


## Inside the widget page

<details>
<summary>Widget Top </summary>

| Field | Value Type | Data Field | Fallback |
|---|---|---|---|
| Image | User Data | `avatar` | — |
| Title | User Data | `display_name` | Custom String: `None` |
| Subtitle 1 | User Data | `username` | — |
| Subtitle 2 | User Data | `listening_since` | — |

</details>

<details>
<summary>Widget Preview </summary>

| Field | Value Type | Data Field |
|---|---|---|
| Contained Image | User Data | `avatar` |

</details>

<details>
<summary>Mini Profile </summary>

| Field | Value Type | Data Field |
|---|---|---|
| Stat (Text) | User Data | `scrobbles_text` |
| Contained Image | User Data | `mini_avatar` |

Stat: Presentation Type `Text`, Label off, Icon off.

</details>

<details>
<summary>Widget Bottom </summary>

| Stat | Data Field | Label |
|---|---|---|
| Stat #1 | `scrobbles` | Total Scrobbles |
| Stat #2 | `loved_tracks` | Tracks Loved |
| Stat #3 | `daily_average` | Daily Average |
| Stat #4 | `tracks` | Unique Tracks |
| Stat #5 | `albums` | Albums Explored |
| Stat #6 | `artists` | Artists Explored |

All stats: Presentation Type `Number`, Value Type `User Data`, Label Value Type `Custom String`.

</details>


## License

MIT. See [LICENSE](LICENSE).
