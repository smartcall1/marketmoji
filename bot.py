import json
import logging
from pathlib import Path
from datetime import time, timezone, timedelta

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERT_HOUR_UTC, ALERT_MINUTE
from fetchers import fetch_all
from interpreter import diagnose
from formatter import build_dashboard
from guide import get_guide
from top_signal import fetch_top_signals, format_top_signal

logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = Path(__file__).parent / "subscribers.json"
KST = timezone(timedelta(hours=9))


def _load_subscribers() -> set[int]:
    if SUBSCRIBERS_FILE.exists():
        try:
            return set(json.loads(SUBSCRIBERS_FILE.read_text()))
        except Exception:
            pass
    subs = set()
    if TELEGRAM_CHAT_ID:
        try:
            subs.add(int(TELEGRAM_CHAT_ID))
        except ValueError:
            pass
    return subs


def _save_subscribers(subs: set[int]) -> None:
    SUBSCRIBERS_FILE.write_text(json.dumps(sorted(subs)))


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subs = _load_subscribers()
    subs.add(chat_id)
    _save_subscribers(subs)
    await update.message.reply_text(
        "\ud83d\udcca \uc2dc\uc7a5 \uac74\uac15\uac80\uc9c4 \ubd07 \uc2dc\uc791!\n\n"
        "\ub9e4\uc77c \uc624\uc804 7\uc2dc(KST) \uac70\uc2dc\uacbd\uc81c \ub300\uc2dc\ubcf4\ub4dc + Top Signal\uc744 \ubcf4\ub0b4\ub4dc\ub9bd\ub2c8\ub2e4.\n\n"
        "\ud83d\udccb \uba85\ub839\uc5b4:\n"
        "  /check  - \uac70\uc2dc\uacbd\uc81c \ub300\uc2dc\ubcf4\ub4dc\n"
        "  /signal - BTC \uc0ac\uc774\ud074 \ud0d1 \uc2dc\uadf8\ub110\n"
        "  /guide  - \uc9c0\ud45c \ud574\uc11d \uac00\uc774\ub4dc\n"
        "  /stop   - \uc54c\ub9bc \uc911\ub2e8"
    )


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subs = _load_subscribers()
    subs.discard(chat_id)
    _save_subscribers(subs)
    await update.message.reply_text("\u23f9\ufe0f \uc54c\ub9bc\uc774 \uc911\ub2e8\ub418\uc5c8\uc2b5\ub2c8\ub2e4. /start \ub85c \ub2e4\uc2dc \uad6c\ub3c5\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.")


async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("\u23f3 \ub370\uc774\ud130 \uc218\uc9d1 \uc911...")
    try:
        data = await fetch_all()
        diag = diagnose(data)
        msg = build_dashboard(diag)
        await update.message.reply_text(msg)
    except Exception as e:
        logger.exception("check failed")
        await update.message.reply_text(f"\u274c \ub370\uc774\ud130 \uc218\uc9d1 \uc2e4\ud328: {e}")


async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Top Signal 데이터 수집 중...")
    try:
        data = await fetch_top_signals()
        msg = format_top_signal(data)
        await update.message.reply_text(msg)
    except Exception as e:
        logger.exception("signal fetch failed")
        await update.message.reply_text(f"❌ Top Signal 수집 실패: {e}")


async def cmd_guide(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    key = ctx.args[0] if ctx.args else None
    msg = get_guide(key)
    if len(msg) > 4096:
        for i in range(0, len(msg), 4096):
            await update.message.reply_text(msg[i:i + 4096])
    else:
        await update.message.reply_text(msg)


async def daily_alert(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Daily alert triggered")

    # \uba54\uc2dc\uc9c0 1: \uac70\uc2dc\uacbd\uc81c \ub300\uc2dc\ubcf4\ub4dc
    try:
        data = await fetch_all()
        diag = diagnose(data)
        msg1 = build_dashboard(diag)
    except Exception as e:
        logger.exception("daily fetch failed")
        msg1 = f"\u274c \uc624\ub298 \ub370\uc774\ud130 \uc218\uc9d1 \uc2e4\ud328: {e}"

    # \uba54\uc2dc\uc9c0 2: Top Signal
    try:
        sig_data = await fetch_top_signals()
        msg2 = format_top_signal(sig_data)
    except Exception as e:
        logger.exception("top signal fetch failed")
        msg2 = f"\u274c Top Signal \uc218\uc9d1 \uc2e4\ud328: {e}"

    subs = _load_subscribers()
    for chat_id in subs:
        try:
            await ctx.bot.send_message(chat_id=chat_id, text=msg1)
            await ctx.bot.send_message(chat_id=chat_id, text=msg2)
        except Exception:
            logger.warning(f"Failed to send to {chat_id}")


def run_bot() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("signal", cmd_signal))
    app.add_handler(CommandHandler("guide", cmd_guide))

    job_queue = app.job_queue
    alert_time = time(hour=ALERT_HOUR_UTC, minute=ALERT_MINUTE, tzinfo=timezone.utc)
    job_queue.run_daily(daily_alert, time=alert_time, name="daily_dashboard")
    logger.info(f"Daily alert scheduled at {alert_time} UTC (07:00 KST)")

    logger.info("Bot started. Polling...")
    app.run_polling(drop_pending_updates=True)
