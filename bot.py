import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ====== تنظیمات ربات ======
BOT_TOKEN = "8333505942:AAEP5G056p5G57yumiuaGQVlZKON0w0ldiY"
ADMIN_ID = 8440703509

# ====== ثبت لاگ ======
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====== مرحله‌های ثبت نام ======
LANGUAGE, PROVINCE = range(2)

languages = ["دری", "پشتو", "انگلیسی"]

provinces = [
    "کابل","غزنی","هرات","مزار","بلخ","ننگرهار","لغمان","پکتیا","پکتیکا","خوست",
    "قندهار","بغلان","پروان","کاپیسا","نورستان","کنر","بدخشان","بامیان","دایکندی",
    "سمنگان","سرپل","فاریاب","جوزجان","هلمند","وردک","فراه","غور","کندز","تخار",
    "پنجشیر","لوگر","زابل","اروزگان","نیمروز"
]

# ====== دیتابیس ساده داخل حافظه ======
users = {}         # اطلاعات کاربر
waiting_users = [] # لیست منتظر برای چت
active_chats = {}  # یوزرها که وصل شدن {user_id: partner_id}
coins = {}         # سکه‌ها

# ====== شروع /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    users[user.id] = {}
    coins[user.id] = 1  # برای تست به هر کاربر ۱ سکه میدیم

    await update.message.reply_text(
        f"سلام {user.first_name}!\n"
        "به ربات چت ناشناس خوش آمدید.\n"
        "لطفا زبان مورد نظر خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([languages], one_time_keyboard=True, resize_keyboard=True)
    )
    return LANGUAGE

# ====== زبان ======
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_language = update.message.text
    users[update.message.from_user.id]["language"] = user_language

    await update.message.reply_text(
        "حالا ولایت خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([provinces[i:i+3] for i in range(0, len(provinces), 3)],
                                         one_time_keyboard=True, resize_keyboard=True)
    )
    return PROVINCE

# ====== ولایت ======
async def set_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_province = update.message.text
    user_id = update.message.from_user.id
    users[user_id]["province"] = user_province

    # پیام به ادمین
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"کاربر جدید ثبت شد ✅\n"
             f"👤 نام: {update.message.from_user.first_name}\n"
             f"🗣 زبان: {users[user_id]['language']}\n"
             f"📍 ولایت: {user_province}\n"
             f"🆔 آیدی: {user_id}"
    )

    # منو اصلی
    menu = [["به ناشناس وصلم کن"], ["راهنما", "موجودی سکه"]]
    await update.message.reply_text("ثبت‌نام شما موفقانه تکمیل شد ✅", 
                                    reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True))
    return ConversationHandler.END

# ====== دکمه ناشناس ======
async def anonymous_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # بررسی سکه برای دخترها
    if users[user_id].get("gender") == "زن" and coins.get(user_id, 0) < 1:
        await update.message.reply_text("❌ شما سکه کافی برای شروع چت ندارید!")
        return
    
    if user_id in waiting_users:
        await update.message.reply_text("⏳ شما در صف جستجو هستید...")
        return

    # جستجو برای جفت
    if waiting_users:
        partner_id = waiting_users.pop(0)

        # وصل کردن
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        # کسر سکه برای زن
        if users[user_id].get("gender") == "زن":
            coins[user_id] -= 1

        await context.bot.send_message(chat_id=user_id, text="✅ شما به یک فرد ناشناس وصل شدید. برای قطع /stop را بزنید.")
        await context.bot.send_message(chat_id=partner_id, text="✅ شما به یک فرد ناشناس وصل شدید. برای قطع /stop را بزنید.")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("🔎 در حال جستجوی یک فرد ناشناس برای شما...")

# ====== ارسال پیام بین دو کاربر ======
async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)

# ====== قطع چت ======
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]

        del active_chats[user_id]
        del active_chats[partner_id]

        await context.bot.send_message(chat_id=user_id, text="❌ شما از چت خارج شدید.")
        await context.bot.send_message(chat_id=partner_id, text="❌ طرف مقابل چت را ترک کرد.")
    else:
        await update.message.reply_text("شما در حال حاضر در چت نیستید.")

# ====== راهنما ======
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 راهنما:\n- /start → ثبت نام\n- به ناشناس وصلم کن → شروع چت\n- /stop → قطع چت\n- موجودی سکه → نمایش تعداد سکه")

# ====== موجودی ======
async def coins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    count = coins.get(user_id, 0)
    await update.message.reply_text(f"💰 موجودی سکه شما: {count}")

# ====== اجرای اصلی ======
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_province)],
        },
        fallbacks=[CommandHandler("cancel", stop_chat)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("coins", coins_cmd))
    app.add_handler(MessageHandler(filters.Regex("به ناشناس وصلم کن"), anonymous_chat))
    app.add_handler(MessageHandler(filters.Regex("راهنما"), help_cmd))
    app.add_handler(MessageHandler(filters.Regex("موجودی سکه"), coins_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_message))

    app.run_polling()

if __name__ == "__main__":
    main()
