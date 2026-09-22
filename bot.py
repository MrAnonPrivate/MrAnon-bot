import os
import io
import logging

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    BotCommand,
    BotCommandScopeChat,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================
# CONFIG
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()

# چند ادمین
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
}


# =========================
# CHECK CONFIG
# =========================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN داخل .env پیدا نشد!")

if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID داخل .env پیدا نشد!")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS داخل .env پیدا نشد!")

CHANNEL_ID = int(CHANNEL_ID)


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# ADMIN CHECK
# =========================

def is_admin(update: Update) -> bool:
    if not update.effective_user:
        return False

    return update.effective_user.id in ADMIN_IDS


async def deny(update: Update):
    if update.message:
        await update.message.reply_text(
            "⛔ شما اجازه استفاده از این ربات را ندارید."
        )


# =========================
# MAIN MENU
# =========================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📤 ارسال پیام",
                callback_data="send"
            ),
            InlineKeyboardButton(
                "🗑 حذف پیام",
                callback_data="delete"
            ),
        ],

        [
            InlineKeyboardButton(
                "👤 مدیریت اعضا",
                callback_data="members"
            ),
            InlineKeyboardButton(
                "📌 پین پیام",
                callback_data="pin"
            ),
        ],

        [
            InlineKeyboardButton(
                "⚙️ مدیریت کانال",
                callback_data="channel"
            ),
            InlineKeyboardButton(
                "📊 آمار",
                callback_data="stats"
            ),
        ],

        [
            InlineKeyboardButton(
                "ℹ️ اطلاعات",
                callback_data="info"
            ),
            InlineKeyboardButton(
                "❌ لغو",
                callback_data="cancel"
            ),
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    context.user_data.pop("action", None)

    await update.message.reply_text(
        "🤖 ربات مدیریت کانال فعال است.\n\n"
        "از منوی زیر استفاده کن:",
        reply_markup=main_menu()
    )


# =========================
# MENU
# =========================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    context.user_data.pop("action", None)

    await update.message.reply_text(
        "📋 منوی مدیریت:",
        reply_markup=main_menu()
    )


# =========================
# HELP
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    text = """
🤖 راهنمای ربات

📤 /send
ارسال پیام به کانال

🗑 /delete MESSAGE_ID
حذف پیام

📌 /pin MESSAGE_ID
پین کردن پیام

📍 /unpin MESSAGE_ID
برداشتن پین

🚫 /ban USER_ID
بن کردن کاربر

✅ /unban USER_ID
آن‌بن کردن کاربر

🖼 /setphoto
تغییر عکس کانال

🗑 /delphoto
حذف عکس کانال

✏️ /settitle TEXT
تغییر نام کانال

📝 /setdescription TEXT
تغییر توضیحات کانال

📊 /stats
آمار کانال

ℹ️ /info
اطلاعات کانال

❌ /cancel
لغو عملیات
"""

    await update.message.reply_text(text)


# =========================
# SEND
# =========================

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    context.user_data["action"] = "send"

    await update.message.reply_text(
        "📤 پیام، عکس، ویدیو، آهنگ، فایل، ویس یا GIF را بفرست.\n\n"
        "من آن را در کانال منتشر می‌کنم.\n\n"
        "برای لغو:\n"
        "/cancel"
    )


# =========================
# DELETE
# =========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ آیدی پیام را وارد کن.\n\n"
            "مثال:\n"
            "/delete 123"
        )
        return

    try:
        message_id = int(context.args[0])

        await context.bot.delete_message(
            chat_id=CHANNEL_ID,
            message_id=message_id
        )

        await update.message.reply_text(
            f"✅ پیام `{message_id}` حذف شد.",
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ نتوانستم پیام را حذف کنم.\n\n"
            "ممکن است Message ID اشتباه باشد یا ربات دسترسی حذف پیام نداشته باشد."
        )


# =========================
# BAN
# =========================

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ آیدی کاربر را وارد کن.\n\n"
            "مثال:\n"
            "/ban 123456789"
        )
        return

    try:

        user_id = int(context.args[0])

        await context.bot.ban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )

        await update.message.reply_text(
            f"🚫 کاربر `{user_id}` بن شد.",
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ عملیات Ban انجام نشد."
        )


# =========================
# UNBAN
# =========================

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ آیدی کاربر را وارد کن.\n\n"
            "مثال:\n"
            "/unban 123456789"
        )
        return

    try:

        user_id = int(context.args[0])

        await context.bot.unban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id,
            only_if_banned=True
        )

        await update.message.reply_text(
            f"✅ کاربر `{user_id}` آن‌بن شد.",
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ عملیات Unban انجام نشد."
        )


# =========================
# SET PHOTO
# =========================

async def setphoto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    context.user_data["action"] = "setphoto"

    await update.message.reply_text(
        "🖼 عکس جدید کانال را ارسال کن."
    )


# =========================
# DELETE PHOTO
# =========================

async def delphoto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    try:

        await context.bot.delete_chat_photo(
            chat_id=CHANNEL_ID
        )

        await update.message.reply_text(
            "✅ عکس کانال حذف شد."
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ حذف عکس کانال انجام نشد."
        )


# =========================
# PIN
# =========================

async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ آیدی پیام را وارد کن.\n\n"
            "مثال:\n"
            "/pin 123"
        )
        return

    try:

        message_id = int(context.args[0])

        await context.bot.pin_chat_message(
            chat_id=CHANNEL_ID,
            message_id=message_id,
            disable_notification=False
        )

        await update.message.reply_text(
            f"📌 پیام `{message_id}` پین شد.",
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ پین کردن پیام انجام نشد."
        )


# =========================
# UNPIN
# =========================

async def unpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ آیدی پیام را وارد کن.\n\n"
            "مثال:\n"
            "/unpin 123"
        )
        return

    try:

        message_id = int(context.args[0])

        await context.bot.unpin_chat_message(
            chat_id=CHANNEL_ID,
            message_id=message_id
        )

        await update.message.reply_text(
            f"📍 پین پیام `{message_id}` برداشته شد.",
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ برداشتن پین انجام نشد."
        )


# =========================
# SET TITLE
# =========================

async def settitle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ نام جدید کانال را وارد کن.\n\n"
            "مثال:\n"
            "/settitle My Channel"
        )
        return

    title = " ".join(context.args)

    try:

        await context.bot.set_chat_title(
            chat_id=CHANNEL_ID,
            title=title
        )

        await update.message.reply_text(
            f"✅ نام کانال به «{title}» تغییر کرد."
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ تغییر نام کانال انجام نشد."
        )


# =========================
# SET DESCRIPTION
# =========================

async def setdescription_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return await deny(update)

    if not context.args:
        await update.message.reply_text(
            "❌ توضیحات جدید را وارد کن.\n\n"
            "مثال:\n"
            "/setdescription My Channel Description"
        )
        return

    description = " ".join(context.args)

    try:

        await context.bot.set_chat_description(
            chat_id=CHANNEL_ID,
            description=description
        )

        await update.message.reply_text(
            "✅ توضیحات کانال تغییر کرد."
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ تغییر توضیحات انجام نشد."
        )


# =========================
# INFO
# =========================

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    try:

        chat = await context.bot.get_chat(CHANNEL_ID)

        text = (
            "ℹ️ اطلاعات کانال\n\n"
            f"📛 نام: {chat.title}\n"
            f"🆔 ID: `{chat.id}`\n"
            f"🔗 Username: @{chat.username if chat.username else 'ندارد'}\n"
            f"👥 نوع: {chat.type}"
        )

        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ دریافت اطلاعات کانال انجام نشد."
        )


# =========================
# STATS
# =========================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    try:

        chat = await context.bot.get_chat(CHANNEL_ID)

        members = await context.bot.get_chat_member_count(
            CHANNEL_ID
        )

        text = (
            "📊 آمار کانال\n\n"
            f"📛 نام: {chat.title}\n"
            f"👥 تعداد اعضا: {members}\n"
            f"🆔 ID: `{CHANNEL_ID}`"
        )

        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ دریافت آمار انجام نشد."
        )


# =========================
# ME
# =========================

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    user = update.effective_user

    await update.message.reply_text(
        "👤 اطلاعات شما\n\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'ندارد'}\n"
        f"ID: `{user.id}`\n\n"
        "✅ شما ادمین ربات هستید.",
        parse_mode="Markdown"
    )


# =========================
# CANCEL
# =========================

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return await deny(update)

    context.user_data.pop("action", None)

    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu()
    )


# =========================
# PROCESS CHANNEL PHOTO
# =========================

async def process_channel_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.photo:
        return

    try:

        photo = update.message.photo[-1]

        file = await context.bot.get_file(
            photo.file_id
        )

        image_bytes = await file.download_as_bytearray()

        image_file = InputFile(
            io.BytesIO(image_bytes),
            filename="channel.jpg"
        )

        await context.bot.set_chat_photo(
            chat_id=CHANNEL_ID,
            photo=image_file
        )

        await update.message.reply_text(
            "✅ عکس کانال با موفقیت تغییر کرد."
        )

        context.user_data.pop("action", None)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ تغییر عکس کانال انجام نشد."
        )


# =========================
# PUBLISH MESSAGE
# =========================

async def publish_to_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    try:

        sent_message = None

        # TEXT
        if message.text:

            sent_message = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message.text
            )

        # PHOTO
        elif message.photo:

            sent_message = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=message.photo[-1].file_id,
                caption=message.caption or None
            )

        # VIDEO
        elif message.video:

            sent_message = await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=message.video.file_id,
                caption=message.caption or None
            )

        # AUDIO
        elif message.audio:

            sent_message = await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=message.audio.file_id,
                caption=message.caption or None
            )

        # DOCUMENT
        elif message.document:

            sent_message = await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=message.document.file_id,
                caption=message.caption or None
            )

        # VOICE
        elif message.voice:

            sent_message = await context.bot.send_voice(
                chat_id=CHANNEL_ID,
                voice=message.voice.file_id,
                caption=message.caption or None
            )

        # ANIMATION / GIF
        elif message.animation:

            sent_message = await context.bot.send_animation(
                chat_id=CHANNEL_ID,
                animation=message.animation.file_id,
                caption=message.caption or None
            )

        else:

            await update.message.reply_text(
                "❌ این نوع پیام پشتیبانی نمی‌شود."
            )

            return

        if sent_message:

            message_id = sent_message.message_id

            await update.message.reply_text(
                "✅ پیام با موفقیت در کانال منتشر شد.\n\n"
                f"🆔 Message ID: `{message_id}`\n\n"
                "🗑 حذف پیام:\n"
                f"`/delete {message_id}`\n\n"
                "📌 پین کردن:\n"
                f"`/pin {message_id}`\n\n"
                "📍 برداشتن پین:\n"
                f"`/unpin {message_id}`",
                parse_mode="Markdown"
            )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ ارسال پیام به کانال انجام نشد.\n\n"
            "دسترسی‌های ربات را بررسی کن."
        )


# =========================
# PROCESS NORMAL MESSAGE
# =========================

async def process_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return

    action = context.user_data.get("action")

    if action == "setphoto":

        if update.message and update.message.photo:

            await process_channel_photo(
                update,
                context
            )

        else:

            await update.message.reply_text(
                "🖼 لطفاً یک عکس ارسال کن."
            )

        return

    if action == "send":

        await publish_to_channel(
            update,
            context
        )

        return


# =========================
# CALLBACK BUTTONS
# =========================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id not in ADMIN_IDS:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )

        return

    await query.answer()

    data = query.data

    # SEND
    if data == "send":

        context.user_data["action"] = "send"

        await query.message.reply_text(
            "📤 پیام، عکس، ویدیو، آهنگ، فایل، ویس یا GIF را بفرست."
        )

    # DELETE
    elif data == "delete":

        await query.message.reply_text(
            "🗑 برای حذف پیام از دستور زیر استفاده کن:\n\n"
            "`/delete MESSAGE_ID`\n\n"
            "مثال:\n"
            "`/delete 123`",
            parse_mode="Markdown"
        )

    # MEMBERS
    elif data == "members":

        await query.message.reply_text(
            "👤 مدیریت اعضا\n\n"
            "🚫 بن:\n"
            "`/ban USER_ID`\n\n"
            "✅ آن‌بن:\n"
            "`/unban USER_ID`",
            parse_mode="Markdown"
        )

    # CHANNEL
    elif data == "channel":

        await query.message.reply_text(
            "⚙️ مدیریت کانال\n\n"
            "🖼 تغییر عکس:\n"
            "`/setphoto`\n\n"
            "🗑 حذف عکس:\n"
            "`/delphoto`\n\n"
            "✏️ تغییر نام:\n"
            "`/settitle نام جدید`\n\n"
            "📝 تغییر توضیحات:\n"
            "`/setdescription توضیحات جدید`",
            parse_mode="Markdown"
        )

    # PIN
    elif data == "pin":

        await query.message.reply_text(
            "📌 پین:\n"
            "`/pin MESSAGE_ID`\n\n"
            "📍 برداشتن پین:\n"
            "`/unpin MESSAGE_ID`",
            parse_mode="Markdown"
        )

    # STATS
    elif data == "stats":

        await stats_command(
            update,
            context
        )

    # INFO
    elif data == "info":

        await info_command(
            update,
            context
        )

    # CANCEL
    elif data == "cancel":

        context.user_data.pop("action", None)

        await query.message.reply_text(
            "❌ عملیات لغو شد."
        )


# =========================
# COMMAND MENU
# =========================

async def setup_commands(application):

    commands = [

        BotCommand("start", "شروع ربات"),
        BotCommand("menu", "منوی مدیریت"),
        BotCommand("send", "ارسال پیام"),
        BotCommand("delete", "حذف پیام"),
        BotCommand("ban", "بن کاربر"),
        BotCommand("unban", "آن‌بن کاربر"),
        BotCommand("setphoto", "تغییر عکس کانال"),
        BotCommand("delphoto", "حذف عکس کانال"),
        BotCommand("pin", "پین پیام"),
        BotCommand("unpin", "برداشتن پین"),
        BotCommand("settitle", "تغییر نام کانال"),
        BotCommand("setdescription", "تغییر توضیحات"),
        BotCommand("info", "اطلاعات کانال"),
        BotCommand("stats", "آمار کانال"),
        BotCommand("me", "اطلاعات ادمین"),
        BotCommand("help", "راهنما"),
        BotCommand("cancel", "لغو"),

    ]

    # ثبت منوی دستورات برای تک‌تک ادمین‌ها
    for admin_id in ADMIN_IDS:

        await application.bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeChat(
                chat_id=admin_id
            )
        )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# =========================
# MAIN
# =========================

def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(setup_commands)
        .build()
    )

    # Commands

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("menu", menu)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("send", send_command)
    )

    application.add_handler(
        CommandHandler("delete", delete_command)
    )

    application.add_handler(
        CommandHandler("ban", ban_command)
    )

    application.add_handler(
        CommandHandler("unban", unban_command)
    )

    application.add_handler(
        CommandHandler("setphoto", setphoto_command)
    )

    application.add_handler(
        CommandHandler("delphoto", delphoto_command)
    )

    application.add_handler(
        CommandHandler("pin", pin_command)
    )

    application.add_handler(
        CommandHandler("unpin", unpin_command)
    )

    application.add_handler(
        CommandHandler("settitle", settitle_command)
    )

    application.add_handler(
        CommandHandler("setdescription", setdescription_command)
    )

    application.add_handler(
        CommandHandler("info", info_command)
    )

    application.add_handler(
        CommandHandler("stats", stats_command)
    )

    application.add_handler(
        CommandHandler("me", me_command)
    )

    application.add_handler(
        CommandHandler("cancel", cancel_command)
    )

    # Buttons

    application.add_handler(
        CallbackQueryHandler(button_callback)
    )

    # Messages

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            process_message
        )
    )

    # Errors

    application.add_error_handler(
        error_handler
    )

    print("BOT STARTED")
    print(f"Admins: {len(ADMIN_IDS)}")

    application.run_polling(
        drop_pending_updates=True
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()