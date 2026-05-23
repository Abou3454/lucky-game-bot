import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1054930340"))
FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL",
    "https://lucky-game-332e1-default-rtdb.firebaseio.com"
)
GAME_URL = os.getenv("GAME_URL", "https://example.com")


def firebase_url(path):
    return f"{FIREBASE_DB_URL.rstrip('/')}/{path}.json"


def get_player(user_id):
    response = requests.get(firebase_url(f"players/{user_id}"), timeout=10)
    response.raise_for_status()

    data = response.json()
    if not data:
        data = {"balance": 0}
        requests.put(firebase_url(f"players/{user_id}"), json=data, timeout=10)

    return data


def set_balance(user_id, balance):
    requests.patch(
        firebase_url(f"players/{user_id}"),
        json={"balance": int(balance)},
        timeout=10
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_player(user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                "افتح اللعبة",
                web_app=WebAppInfo(url=GAME_URL)
            )
        ]
    ]

    await update.message.reply_text(
        f"🎉 أهلاً وسهلاً {user.first_name}\n\n"
        f"اجمع النقاط وادخل السحب الأسبوعي 🎁\n\n"
        f"كل 7500 نقطة = تذكرة واحدة في السحب.\n"
        f"كلما جمعت نقاط أكثر زادت فرصتك بالفوز.\n\n"
        f"🆔 ID الشحن الخاص بك:\n"
        f"{user.id}\n\n"
        f"👇 اضغط الزر بالأسفل وابدأ اللعب الآن.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ID الشحن الخاص بك:\n{update.effective_user.id}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر للإدارة فقط.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("استخدم الأمر هكذا:\n/balance ID")
        return

    user_id = context.args[0]
    player = get_player(user_id)
    await update.message.reply_text(f"رصيد {user_id} هو: {player.get('balance', 0)}")


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر للإدارة فقط.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("استخدم الأمر هكذا:\n/add ID amount")
        return

    user_id = context.args[0]

    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("المبلغ يجب أن يكون رقماً.")
        return

    player = get_player(user_id)
    old_balance = int(player.get("balance", 0))
    new_balance = old_balance + amount

    set_balance(user_id, new_balance)

    await update.message.reply_text(
        f"تم شحن اللاعب بنجاح.\n"
        f"ID: {user_id}\n"
        f"المبلغ: {amount}\n"
        f"الرصيد الجديد: {new_balance}"
    )


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر للإدارة فقط.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("استخدم الأمر هكذا:\n/remove ID amount")
        return

    user_id = context.args[0]

    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("المبلغ يجب أن يكون رقماً.")
        return

    player = get_player(user_id)
    old_balance = int(player.get("balance", 0))
    new_balance = max(0, old_balance - amount)

    set_balance(user_id, new_balance)

    await update.message.reply_text(
        f"تم الخصم من اللاعب.\n"
        f"ID: {user_id}\n"
        f"المبلغ: {amount}\n"
        f"الرصيد الجديد: {new_balance}"
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Add it in environment variables.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
