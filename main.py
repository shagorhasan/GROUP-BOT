import os, random, logging, sqlite3, time
from datetime import date
from google import genai
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
log=logging.getLogger("loudwin")
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
KEY=os.getenv("GEMINI_API_KEY","").strip()
MODEL=os.getenv("GEMINI_MODEL","gemini-3.8-flash").strip()
gid=os.getenv("TELEGRAM_GROUP_ID","").strip()
GROUP_ID=int(gid) if gid.lstrip("-").isdigit() else None
DB_PATH=os.getenv("BOT_DB_PATH","loud_win_zone.db")
client=genai.Client(api_key=KEY) if KEY else None
enabled=set()
history={}
last_xp={}

STYLE="""তুমি LOUD WIN ZONE Telegram গ্রুপের প্রাণবন্ত AI আড্ডা সঙ্গী। স্বাভাবিক বাংলা বা Banglish-এ সংক্ষিপ্ত, মজার, ইউনিক এবং বন্ধুত্বপূর্ণ উত্তর দেবে। হালকা রোস্ট করা যায়, কিন্তু ঘৃণা, হুমকি, হয়রানি বা ব্যক্তিগত অপমান নয়। নিজেকে মানুষ বলবে না। সাধারণত ১-৪টি বাক্য এবং অল্প emoji ব্যবহার করবে।"""

JOKES=["😂 ভাই, তোর প্ল্যান শুনে Wi-Fi-ও কানেকশন ছেড়ে দিল!","🤣 এত সিরিয়াস কেন? এটা আড্ডা, বোর্ড পরীক্ষার হল না!","😎 LOUD WIN ZONE-এ ঢুকেছিস, হাসির জন্য প্রস্তুত থাক!","🔥 আড্ডা জমাও, বন্ধুত্বটা VIP রাখো!","🎮 গেমে হারলে সমস্যা নেই, অজুহাতে বিশ্বরেকর্ড করো না!"]
TRUTHS=["🤔 Truth: তোমার সবচেয়ে মজার ভুল কোনটা?","🤔 Truth: কোন গেমে সবচেয়ে বেশি rage করো?","🤔 Truth: গ্রুপে সবচেয়ে বেশি হাসায় কে?"]
DARES=["🔥 Dare: পরের ৩টি মেসেজে শুধু emoji দাও!","🔥 Dare: কাউকে একটা genuine compliment দাও ❤️","🔥 Dare: তোমার mood ৩টি emoji দিয়ে বোঝাও!"]
CHALLENGES=["🎯 আজ ৩ জনকে ভালো কথা বলো!","🎯 আজ অন্তত একজনকে হাসাও 😂","🎯 তোমার প্রিয় গেমের নাম বলো 🎮"]

def db():
 c=sqlite3.connect(DB_PATH)
 c.execute("CREATE TABLE IF NOT EXISTS scores(chat INTEGER,user INTEGER,name TEXT,points INTEGER DEFAULT 0,messages INTEGER DEFAULT 0,last_daily TEXT,PRIMARY KEY(chat,user))")
 c.commit(); return c

async def ai(chat,user,prompt):
 if not client: return "⚠️ GEMINI_API_KEY সেট করা হয়নি। Render Environment Variables-এ যোগ করো।"
 key=(chat,user); hist=history.setdefault(key,[])
 # Use recent text context; keep each request bounded.
 contents=STYLE+"\\n\\nConversation so far:\\n"+"\\n".join(f"{r}: {t}" for r,t in hist[-6:])+"\\nUser: "+prompt
 try:
  response=await client.aio.models.generate_content(model=MODEL,contents=contents)
  answer=(response.text or "").strip() or "একটু গ্লিচ হলো বস 😅 আবার বলো!"
  hist.extend([("User",prompt),("Bot",answer)]); history[key]=hist[-8:]
  return answer[:3900]
 except Exception:
  log.exception("Gemini API failed")
  return "দুঃখিত ভাই, AI-তে একটু সমস্যা হচ্ছে। API key, model ও quota চেক করো।"

async def start(u,c):
 await u.effective_message.reply_text("🔥 LOUD WIN ZONE AI-তে স্বাগতম!\\nবাংলা/Banglish AI আড্ডা, Truth/Dare, XP, Quiz-style challenge ও Auto Chat আছে।\\n/help লিখে কমান্ড দেখো।")
async def help_cmd(u,c):
 await u.effective_message.reply_text("🤖 LOUD WIN ZONE COMMANDS\\n/chat তোমার কথা — Gemini AI\\n/joke — জোক\\n/truth /dare /mood /challenge\\n/daily /profile /leaderboard\\n/enablechat /stopchat\\n/start /help")
async def chat_cmd(u,c):
 msg=u.effective_message
 prompt=" ".join(c.args).strip()
 if not prompt and msg.reply_to_message and msg.reply_to_message.text: prompt=msg.reply_to_message.text
 if not prompt: await msg.reply_text("ব্যবহার: /chat আজকের আড্ডা কেমন?"); return
 await msg.reply_chat_action("typing")
 await msg.reply_text(await ai(u.effective_chat.id,u.effective_user.id,prompt))
async def joke(u,c): await u.effective_message.reply_text(random.choice(JOKES))
async def truth(u,c): await u.effective_message.reply_text(random.choice(TRUTHS))
async def dare(u,c): await u.effective_message.reply_text(random.choice(DARES))
async def mood(u,c): await u.effective_message.reply_text("🎭 Mood check! 😎 😂 😴 😡 🥳 ❤️ — কোনটা তোমার mood?")
async def challenge(u,c): await u.effective_message.reply_text(random.choice(CHALLENGES))

async def xp(u,points,messages=0):
 user,chat=u.effective_user,u.effective_chat
 if not user or not chat or user.is_bot:return
 con=db()
 con.execute("INSERT INTO scores(chat,user,name,points,messages) VALUES(?,?,?,?,?) ON CONFLICT(chat,user) DO UPDATE SET name=excluded.name,points=points+?,messages=messages+?",(chat.id,user.id,user.full_name,points,messages,points,messages))
 con.commit();con.close()
async def daily(u,c):
 user,chat=u.effective_user,u.effective_chat
 con=db(); row=con.execute("SELECT last_daily FROM scores WHERE chat=? AND user=?",(chat.id,user.id)).fetchone()
 today=date.today().isoformat()
 if row and row[0]==today:
  await u.effective_message.reply_text("⏳ আজকের reward নিয়েছো! কাল আবার এসো.")
 else:
  con.execute("INSERT INTO scores(chat,user,name,points,last_daily) VALUES(?,?,?,?,?) ON CONFLICT(chat,user) DO UPDATE SET name=excluded.name,points=points+10,last_daily=excluded.last_daily",(chat.id,user.id,user.full_name,10,today)); con.commit()
  await u.effective_message.reply_text("🎁 Daily reward: +10 XP!")
 con.close()
async def profile(u,c):
 user,chat=u.effective_user,u.effective_chat; con=db()
 row=con.execute("SELECT points,messages FROM scores WHERE chat=? AND user=?",(chat.id,user.id)).fetchone();con.close()
 pts,msgs=row if row else (0,0)
 await u.effective_message.reply_text(f"👤 {user.full_name}\\n⭐ XP: {pts}\\n🏅 Level: {pts//100+1}\\n💬 Messages: {msgs}")
async def leaderboard(u,c):
 chat=u.effective_chat;con=db();rows=con.execute("SELECT name,points FROM scores WHERE chat=? ORDER BY points DESC LIMIT 10",(chat.id,)).fetchall();con.close()
 if not rows: await u.effective_message.reply_text("🏆 Leaderboard খালি। /daily দিয়ে XP নাও!");return
 await u.effective_message.reply_text("🏆 LOUD WIN ZONE TOP 10\\n"+"\\n".join(f"{['🥇','🥈','🥉'][i] if i<3 else str(i+1)+'.'} {n}: {p} XP" for i,(n,p) in enumerate(rows)))
def schedule(c,chat): c.job_queue.run_once(auto,random.randint(300,600),chat_id=chat,name=f"auto-{chat}",data={"chat":chat})
async def enable(u,c):
 chat=u.effective_chat
 if not chat or chat.type not in (ChatType.GROUP,ChatType.SUPERGROUP): await u.effective_message.reply_text("গ্রুপে ব্যবহার করো।");return
 if GROUP_ID and chat.id!=GROUP_ID: await u.effective_message.reply_text("এটি configured group নয়।");return
 enabled.add(chat.id);await u.effective_message.reply_text("🔥 AI Auto Chat চালু! প্রতি ৫–১০ মিনিটে মজার AI পোস্ট হবে। /stopchat দিয়ে বন্ধ করো।");schedule(c,chat.id)
async def stop(u,c):
 chat=u.effective_chat;enabled.discard(chat.id)
 for j in c.job_queue.get_jobs_by_name(f"auto-{chat.id}"):j.schedule_removal()
 await u.effective_message.reply_text("⏹️ Auto Chat বন্ধ।")
async def auto(c):
 chat=c.job.data["chat"]
 if chat not in enabled:return
 prompt=random.choice(["গ্রুপের জন্য ছোট মজার বাংলা icebreaker লেখো।","LOUD WIN ZONE-এর জন্য বন্ধুত্বপূর্ণ গেমিং জোক লেখো।","সবাইকে উত্তর দিতে উৎসাহিত করে এমন মজার প্রশ্ন করো।","কাউকে নির্দিষ্ট না করে হালকা friendly roast লেখো।"])
 try: await c.bot.send_message(chat_id=chat,text=await ai(chat,0,prompt))
 except Exception: log.exception("Auto chat failed")
 finally:
  if chat in enabled:schedule(c,chat)
async def welcome(u,c):
 for m in u.effective_message.new_chat_members:
  if not m.is_bot: await u.effective_message.reply_text(f"🎉 স্বাগতম {m.full_name}! ❤️ LOUD WIN ZONE পরিবারে আড্ডা জমাও। /help দেখো!")
async def group_msg(u,c):
 msg=u.effective_message; chat=u.effective_chat; user=u.effective_user
 if not msg or not msg.text or not chat:return
 if user and not user.is_bot and time.time()-last_xp.get((chat.id,user.id),0)>60:
  last_xp[(chat.id,user.id)]=time.time();await xp(u,1,1)
 uname=c.bot.username or ""
 mentioned=uname and "@"+uname.lower() in msg.text.lower()
 replied=msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.id==c.bot.id
 trigger=msg.text.lower().startswith(("bot ","বট ","oi bot","ওই বট"))
 if mentioned or replied or trigger:
  prompt=msg.text.replace("@"+uname,"") if uname else msg.text
  await msg.reply_chat_action("typing")
  await msg.reply_text(await ai(chat.id,user.id if user else 0,prompt))
async def err(u,c): log.error("Bot error: %s",c.error)
def main():
 if not TOKEN: raise RuntimeError("Set TELEGRAM_BOT_TOKEN in Render environment.")
 if not KEY: log.warning("GEMINI_API_KEY missing; AI replies unavailable.")
 con=db();con.close()
 app=Application.builder().token(TOKEN).build()
 for name,fn in [("start",start),("help",help_cmd),("chat",chat_cmd),("joke",joke),("truth",truth),("dare",dare),("mood",mood),("challenge",challenge),("daily",daily),("profile",profile),("leaderboard",leaderboard),("enablechat",enable),("stopchat",stop)]:
  app.add_handler(CommandHandler(name,fn))
 app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,welcome))
 app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,group_msg))
 app.add_error_handler(err)
 app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__=="__main__":main()
