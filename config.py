import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ALERT_HOUR_UTC = 22  # 07:00 KST = 22:00 UTC (전날)
ALERT_MINUTE = 0

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30

CAPE_THRESHOLDS = [
    (15, 1, "\U0001f7e2", "\ub300\uc138\uc77c"),
    (20, 2, "\U0001f7e2", "\uad1c\ucc2e\uc740 \uac00\uaca9"),
    (25, 3, "\U0001f7e1", "\ubcf4\ud1b5"),
    (30, 4, "\U0001f7e0", "\uc880 \ube44\uc300"),
    (40, 4, "\U0001f534", "\ub9ce\uc774 \ube44\uc300"),
    (999, 5, "\U0001f480", "\uc5ed\ub300\uae09"),
]

ECY_THRESHOLDS = [
    (-999, 5, "\U0001f534", "\ucc44\uad8c\uc774 \ub0ab\ub2e4"),
    (0, 5, "\U0001f534", "\ucc44\uad8c\uc774 \ub0ab\ub2e4"),
    (1, 4, "\U0001f7e0", "\uc8fc\uc2dd \ub9e4\ub825 \uc5c6\uc74c"),
    (2, 3, "\U0001f7e1", "\ube44\uc2b7\ube44\uc2b7"),
    (4, 2, "\U0001f7e2", "\uc8fc\uc2dd \uad1c\ucc2e\uc74c"),
    (999, 1, "\U0001f7e2", "\uc8fc\uc2dd \uc0ac\ub77c"),
]

BUFFETT_THRESHOLDS = [
    (70, 1, "\U0001f7e2", "\ub300\uc138\uc77c"),
    (100, 2, "\U0001f7e2", "\uc801\ub2f9"),
    (115, 3, "\U0001f7e1", "\ubcf4\ud1b5"),
    (140, 4, "\U0001f7e0", "\ubd80\ud480"),
    (180, 4, "\U0001f534", "\ub9ce\uc774 \ubd80\ud480"),
    (9999, 5, "\U0001f480", "\uc5ed\ub300\uae09 \uac70\ud488"),
]

YIELD_CURVE_THRESHOLDS = [
    (-999, 5, "\U0001f480", "\uce68\uccb4 \uacbd\uace0"),
    (0, 5, "\U0001f534", "\uce68\uccb4 \uacbd\uace0"),
    (0.5, 4, "\U0001f7e1", "\ub458\ud654 \uc911"),
    (1, 3, "\U0001f7e2", "\uad1c\ucc2e\uc74c"),
    (2, 2, "\U0001f7e2", "\uc88b\uc74c"),
    (999, 1, "\U0001f7e2", "\uac15\ud55c \ud655\uc7a5"),
]

VIX_THRESHOLDS = [
    (15, 5, "\U0001f634", "\ub108\ubb34 \ud3c9\uc628"),
    (20, 4, "\U0001f610", "\ud3c9\ubc94"),
    (25, 3, "\U0001f630", "\ubd88\uc548"),
    (30, 2, "\U0001f628", "\uacb8\uba39\uc74c"),
    (40, 1, "\U0001f631", "\ud328\ub2c9"),
    (999, 1, "\U0001f92f", "\uadf9\ud55c \uacf5\ud3ec"),
]

FG_STOCK_THRESHOLDS = [
    (25, 1, "\U0001f631", "\uadf9\ub2e8\uc801 \uacf5\ud3ec"),
    (45, 2, "\U0001f630", "\uacf5\ud3ec"),
    (55, 3, "\U0001f610", "\ubcf4\ud1b5"),
    (75, 4, "\U0001f60f", "\uc695\uc2ec"),
    (100, 5, "\U0001f911", "\uadf9\ub2e8\uc801 \ud0d0\uc695"),
]

FG_CRYPTO_THRESHOLDS = [
    (25, 1, "\U0001f631", "\uadf9\ub2e8\uc801 \uacf5\ud3ec"),
    (45, 2, "\U0001f630", "\uacf5\ud3ec"),
    (55, 3, "\U0001f610", "\ubcf4\ud1b5"),
    (75, 4, "\U0001f60f", "\uc695\uc2ec"),
    (100, 5, "\U0001f911", "\uadf9\ub2e8\uc801 \ud0d0\uc695"),
]
