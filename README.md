# LOUD WIN ZONE — Gemini AI Telegram Bot

## Features
- Gemini-powered Bangla/Banglish chat, friendly jokes and group replies
- `/chat`, `/joke`, `/truth`, `/dare`, `/mood`, `/challenge`
- XP, level, `/daily`, `/profile`, `/leaderboard`
- Welcome message for new members
- `/enablechat` sends AI icebreakers/jokes every random 5–10 minutes; `/stopchat` stops them
- SQLite stores XP/daily reward data

## Security
Never put API keys or Telegram tokens in source code or GitHub. Use Render Environment Variables only. If a key was shared in a chat/public place, revoke it and create a fresh one.

## Render setup
1. Create a Telegram bot using @BotFather and copy its token.
2. Upload these files to GitHub.
3. Create a Render Background Worker.
4. Set environment variables:
   - `TELEGRAM_BOT_TOKEN` = BotFather token
   - `GEMINI_API_KEY` = key from https://aistudio.google.com/apikey
   - `GEMINI_MODEL` = `gemini-3.8-flash` (use a model available to your account)
   - `TELEGRAM_GROUP_ID` = optional target group ID
5. Deploy, add bot to your group, then send `/enablechat`.

## Commands
`/start` `/help` `/chat message` `/joke` `/truth` `/dare` `/mood` `/challenge` `/daily` `/profile` `/leaderboard` `/enablechat` `/stopchat`

Notes: Gemini usage is subject to current quotas/terms. Auto-chat enabled state resets on worker restart, so run `/enablechat` again. SQLite persistence depends on Render storage; use a persistent disk and set `BOT_DB_PATH` to keep data through redeploys. Bot privacy settings may limit messages it can see; mentions/replies are reliable triggers.
