
import os
import re
from urllib.parse import quote_plus

import phonenumbers
from phonenumbers import PhoneNumberFormat
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = (
    os.getenv("BOT_TOKEN")
    or os.getenv("TELEGRAM_BOT_TOKEN")
)

if not TOKEN:
    raise RuntimeError(
        "Добавь BOT_TOKEN или TELEGRAM_BOT_TOKEN в настройках хостинга."
    )

MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📱 Проверить телефон"),
         KeyboardButton("🔎 Искать упоминания")],
        [KeyboardButton("👤 Проверить @username"),
         KeyboardButton("ℹ️ Помощь")],
    ],
    resize_keyboard=True,
)

def search_links(query):
    q = quote_plus(query)
    return (
        f"Google: https://www.google.com/search?q={q}\n"
        f"Bing: https://www.bing.com/search?q={q}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "🔎 OSINT-бот запущен!\n\n"
        "Выбери действие в меню ниже.\n"
        "Я работаю с публичными источниками и "
        "не подтверждаю личность владельца номера.",
        reply_markup=MENU,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
 
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Как пользоваться:\n\n"
        "📱 Проверить телефон — формат, регион и тип.\n"
        "🔎 Искать упоминания — ссылки на поиск номера.\n"
        "👤 Проверить @username — ссылка на публичный профиль "
        "и поиск упоминаний ника.\n\n"
        "Можно также отправить номер или @username напрямую.",
        reply_markup=MENU,
    )

async def phone_report(update, text, search=False):
    try:
        number = phonenumbers.parse(
            text.strip(),
            None if text.strip().startswith("+") else "AM",
        )

        possible = phonenumbers.is_possible_number(number)
        valid = phonenumbers.is_valid_number(number)
        region = phonenumbers.region_code_for_number(number) or "Не определён"
        formatted = phonenumbers.format_number(
            number, PhoneNumberFormat.INTERNATIONAL
        )
        national = phonenumbers.format_number(
            number, PhoneNumberFormat.NATIONAL
        )

        kind = phonenumbers.number_type(number)
        type_names = {
            0: "Стационарный",
            1: "Мобильный",
            2: "Стационарный или мобильный",
            3: "Бесплатный номер",
            4: "Платный номер",
            5: "Общий платный номер",
            6: "VoIP",
            7: "Персональный номер",
            8: "Пейджер",
            9: "Неизвестный",
            10: "Неизвестный",
        }

        report = (
            "📋 ОТЧЁТ ПО НОМЕРУ\n\n"
            f"Номер: {formatted}\n"
            f"Национальный формат: {national}\n"
            f"Регион плана нумерации: {region}\n"
            f"Возможная длина и формат: {'Да' if possible else 'Нет'}\n"
            f"Соответствует плану нумерации: {'Да' if valid else 'Нет'}\n"
            f"Тип: {type_names.get(kind, 'Не определён')}\n\n"
            "⚠️ Это техническая проверка. Она не доказывает, "
            "что номер активен или кому-либо принадлежит."
        )

        if search:
            report += "\n\n🔎 Поиск публичных упоминаний:\n" + search_links(
                f'"{formatted}" OR "{text.strip()}"'
            )

        await update.message.reply_text(report, reply_markup=MENU)

    except (phonenumbers.NumberParseException, ValueError):
        await update.message.reply_text(
            "Не удалось разобрать номер.\n"
            "Введи номер с кодом страны, например +374...",
            reply_markup=MENU,
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    if text == "📱 Проверить телефон":
        context.user_data["mode"] = "phone"
        await update.message.reply_text(
            "Отправь номер с кодом страны, например +374...",
            reply_markup=MENU,
        )
        return

    if text == "🔎 Искать упоминания":
        context.user_data["mode"] = "search"
        await update.message.reply_text(
            "Отправь номер телефона в международном формате.",
            reply_markup=MENU,
        )
        return

    if text == "👤 Проверить @username":
        context.user_data["mode"] = "username"
        await update.message.reply_text(
            "Отправь публичный никнейм, например @example.",
            reply_markup=MENU,
        )
        return

    if text == "ℹ️ Помощь":
        await help_command(update, context)
        return

    if text.startswith("@") or mode == "username":
        username = text.lstrip("@").strip()

        if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
            await update.message.reply_text(
                "Проверь формат никнейма. Отправь @username.",
                reply_markup=MENU,
            )
            return

        context.user_data["mode"] = None
        await update.message.reply_text(
            f"👤 ОТЧЁТ ПО НИКНЕЙМУ\n\n"
            f"Никнейм: @{username}\n"
            f"Публичная ссылка: https://t.me/{username}\n\n"
            f"🔎 Поиск публичных упоминаний:\n"
            f"{search_links('"' + username + '"')}\n\n"
            "⚠️ Ссылка не подтверждает личность владельца.",
            reply_markup=MENU,
        )
        return

    if mode in ("phone", "search") or re.search(r"\d", text):
        context.user_data["mode"] = None
        await phone_report(
            update,
            text,
            search=(mode == "search"),
        )
        return

    await update.message.reply_text(
        "Выбери действие в меню или отправь номер телефона либо @username.",
        reply_markup=MENU,
    )

async def error_handler(update, context):
    print(f"Ошибка обработки обновления: {context.error!r}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    app.add_error_handler(error_handler)
    print("OSINT-бот запускается...")
    app.run_polling()

if __name__ == "__main__":
    main()

