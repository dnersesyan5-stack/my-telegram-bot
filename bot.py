
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ["BOT_TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🔎 Я OSINT-бот.\n\n"
        "Отправь номер телефона или @username.\n\n"
        "Я проверю формат и помогу найти публичный профиль."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("@"):
        username = text[1:]

        if re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
            await update.message.reply_text(
                f"Имя выглядит корректно.\n"
                f"Публичная ссылка:\nhttps://t.me/{username}\n\n"
                "Это не подтверждает, что аккаунт существует."
            )
        else:
            await update.message.reply_text(
                "Имя выглядит некорректно. Проверь @username."
            )

    else:
        phone = re.sub(r"[\s()-]", "", text)

        if re.fullmatch(r"\+?[0-9]{7,15}", phone):
            await update.message.reply_text(
                f"Формат номера выглядит допустимым: {phone}\n"
                "Это не подтверждает владельца или существование номера."
            )
        else:
            await update.message.reply_text(
                "Не понял ввод 😅\n"
                "Отправь номер телефона или @username."
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправь мне номер телефона или @username.\n"
        "/start — запуск\n"
        "/help — помощь"
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Бот запущен!")
app.run_polling()
