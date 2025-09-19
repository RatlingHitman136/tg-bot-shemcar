#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import datetime
from collections import deque


from msgObject import MsgObject

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timezone, timedelta

import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackContext,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

GETTING_INFO = 0

# list of updates that admin sends
admin_list = []
allowed_ids = []
ALLOWED_IDS_FILE_PATH = "allowed_ids.txt"
TOKEN_FILE_PATH ="token.txt"

working_timezone = timezone(timedelta(hours=2))
start_working_time = datetime.time(hour=8, minute=0, tzinfo=working_timezone)  # 8:00 AM
end_working_time = datetime.time(hour=19, minute=0, tzinfo=working_timezone)  # 5:00 PM
working_days = (0, 1, 2, 3, 4, 5, 6)  # from Monday (0) to Sunday (6)

saved_msg = deque()


def facts_to_str(user_data: dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_html(
        "<b>Вітаю!</b>\n\n" +
        "Повний перелік послуг та цін можна подивитись на сайті: https://shemcar.com.ua.\n\n" +
        "<a href=\"https://maps.app.goo.gl/5MvE5jPPe1u3ZWK8A\"> Адреса: Рідна, 52б, Забуччя, Київська область, 08102</a>\n\n" +
        "Розклад роботи СТО та Шиномонтажу: Вт - Сб, 9:00 - 18:00.\n\n" +
        "Контактний номер телефону: 067 250 0550.\n"
    )
    await update.message.reply_text(
        "Для зворотнього зв'язку, напишіть одним повідомленням: ім’я, номер телефону, VIN (за потреби) та коротко опишіть питання, яке вас цікавить.\n\n" +
        "Для завершення спілкування введіть команду: /end")
    return GETTING_INFO


async def send_all_admins_msg(msg: MsgObject) -> None:
    for admin in admin_list:
        await admin.message.reply_html(msg.to_html())


async def send_saved_msg() -> None:
    msg = saved_msg.popleft()
    if len(admin_list) == 0:
        logger.error("Tried to send msg, when there was no active admins")
    for admin in admin_list:
        await admin.message.reply_html(msg.to_html())


async def try_send_all_saved_msg() -> None:
    while len(saved_msg) and len(admin_list) != 0:
        await send_saved_msg()


def is_now_working_hour() -> bool:
    now = datetime.datetime.now(tz=working_timezone)
    current_time = now.time()

    # Make sure current_time has timezone info
    current_time = current_time.replace(tzinfo=working_timezone)

    # Check if current day is a workday
    is_workday = now.weekday() in working_days

    # Check if current time is within working hours
    is_work_hour = start_working_time <= current_time < end_working_time

    return is_workday and is_work_hour


async def received_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    received_msg = update.message.text
    user = update.effective_user

    msg = MsgObject.create(received_msg, user, datetime.datetime.now(working_timezone))

    if len(admin_list) != 0 and is_now_working_hour():
        await send_all_admins_msg(msg)
    else:
        saved_msg.append(msg)

    await update.message.reply_text("Дякуємо! Ваш запит зареєстровано. Менеджер зв’яжеться з вами у найближчий робочий час.")
    await update.message.reply_text("Для початку нового спілкування введіть команду /start")
    return ConversationHandler.END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Для початку нового спілкування введіть команду /start")
    return ConversationHandler.END


async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in allowed_ids:
        is_already_added = False
        for admin_update in admin_list:
            if user_id == admin_update.effective_user.id:
                is_already_added = True
        if is_already_added:
            await update.message.reply_text("You are already among active Admins")
        else:
            await update.message.reply_text("You are added to active Admins")
            admin_list.append(update)
            await try_send_all_saved_msg()
    else:
        await update.message.reply_text("Your ID is not among Admin IDs")


async def admin_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in allowed_ids:
        for admin_update in admin_list:
            if admin_update.effective_user.id == user_id:
                admin_list.remove(admin_update)
                await update.message.reply_text("You are removed from active Admins")
    else:
        await update.message.reply_text("Your ID is not among Admin IDs")


def morning_send_all_wrapper():
    asyncio.run(morning_send_all())


async def morning_send_all():
    print("function atleast executed")
    logger.info(f"Executing scheduled morning task at {start_working_time}")
    await try_send_all_saved_msg()

def init_allowed_ids():
    try:
        with open(ALLOWED_IDS_FILE_PATH, 'r') as file:
            for line_number, line in enumerate(file, 1):
                # Remove comments and strip whitespace
                clean_line = line.split('#')[0].strip()

                # Skip empty lines
                if not clean_line:
                    continue

                # Check if line starts with a number
                if not clean_line[0].isdigit():
                    raise ValueError(f"Line {line_number} doesn't start with a number: {line.strip()}")

                # Extract the number from the beginning
                number_str = ''
                for char in clean_line:
                    if char.isdigit():
                        number_str += char
                    else:
                        break

                allowed_ids.append(int(number_str))
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find allowed IDs file at {ALLOWED_IDS_FILE_PATH}")

def read_token() -> str:
    try:
        with open(TOKEN_FILE_PATH, 'r') as file:
            token = file.readline()
            return token.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find token file at {TOKEN_FILE_PATH}")


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    init_allowed_ids()
    token = read_token()
    application = Application.builder().token(token).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GETTING_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_info)
            ]
        },
        fallbacks=[CommandHandler("end", end)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("admin_start", admin_start))
    application.add_handler(CommandHandler("admin_stop", admin_stop))

    scheduler = BackgroundScheduler(timezone=working_timezone, job_defaults={'misfire_grace_time': 10})
    scheduler.add_job(morning_send_all_wrapper,
                      CronTrigger(hour=start_working_time.hour, minute=start_working_time.minute))

    # application.job_queue.scheduler_configuration.update({'misfire_grace_time': 100})
    # application.job_queue.scheduler = scheduler
    # application.job_queue.run_daily(morning_send_all, time=start_working_time, days=working_days)

    # Run the bot until the user presses Ctrl-C
    scheduler.start()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
