from config import (
    CAPE_THRESHOLDS, ECY_THRESHOLDS, BUFFETT_THRESHOLDS,
    YIELD_CURVE_THRESHOLDS, VIX_THRESHOLDS,
    FG_STOCK_THRESHOLDS, FG_CRYPTO_THRESHOLDS,
)


def _interpret(value: float, thresholds: list) -> tuple[int, str, str]:
    for ceiling, score, emoji, desc in thresholds:
        if value <= ceiling:
            return score, emoji, desc
    last = thresholds[-1]
    return last[1], last[2], last[3]


def interpret_cape(v: float) -> tuple[int, str, str]:
    return _interpret(v, CAPE_THRESHOLDS)

def interpret_ecy(v: float) -> tuple[int, str, str]:
    return _interpret(v, ECY_THRESHOLDS)

def interpret_buffett(v: float) -> tuple[int, str, str]:
    return _interpret(v, BUFFETT_THRESHOLDS)

def interpret_yield_curve(v: float) -> tuple[int, str, str]:
    return _interpret(v, YIELD_CURVE_THRESHOLDS)

def interpret_vix(v: float) -> tuple[int, str, str]:
    return _interpret(v, VIX_THRESHOLDS)

def interpret_fg_stock(v: int) -> tuple[int, str, str]:
    return _interpret(v, FG_STOCK_THRESHOLDS)

def interpret_fg_crypto(v: int) -> tuple[int, str, str]:
    return _interpret(v, FG_CRYPTO_THRESHOLDS)


MATRIX = {
    ("expensive", "fear"): ("\ud63c\uc870\u00b7\ubd84\ud560\ub9e4\uc218", "\U0001f7e1",
        "\ube44\uc2f8\uc9c0\ub9cc \uacb8\ub3c4 \ub0ac\ub2e4 = \ud63c\uc870\n"
        "\u2022 \uc62c\uc778 \uc704\ud5d8, \ubd84\ud560\ub9e4\uc218\uac00 \ucd5c\uc120\n"
        "\u2022 \uacf5\ud3ec \ub354 \ucee4\uc9c0\uba74 \ube44\uc911 \ud655\ub300"),
    ("expensive", "neutral"): ("\uace0\uc810\uc8fc\uc758", "\U0001f7e0",
        "\ube44\uc2fc\ub370 \uc544\ubb34\ub3c4 \uc548 \ubb34\uc11c\uc6cc\ud568 = \uc704\ud5d8\n"
        "\u2022 \uc2dc\uc7a5 \uc790\ub9cc \uc911, \uae09\ub77d \uac00\ub2a5\n"
        "\u2022 \uc2e0\uaddc\uc9c4\uc785 \ucd5c\uc18c\ud654\n"
        "\u2022 VIX 35+ \uc62c \ub54c\uae4c\uc9c0 \ub300\uae30"),
    ("expensive", "greed"): ("\U0001f6a8\ub3c4\ub9dd\uccd0", "\U0001f534",
        "\ube44\uc2f8\uace0 \ud0d0\uc695 = \uac00\uc7a5 \uc704\ud5d8\n"
        "\u2022 \ub808\ubc84\ub9ac\uc9c0\u00b7\ucd94\uaca9\ub9e4\uc218 \uae08\uc9c0\n"
        "\u2022 \ud604\uae08\ud655\ubcf4 + \ub9ac\uc2a4\ud06c \ucd95\uc18c"),
    ("normal", "fear"): ("\uae30\ud68c\ud0d0\uc0c9", "\U0001f7e2",
        "\uc801\ub2f9\ud55c \uac00\uaca9\uc5d0 \uacf5\ud3ec = \uae30\ud68c\n"
        "\u2022 \ubd84\ud560\ub9e4\uc218 \uc2dc\uc791 OK\n"
        "\u2022 \uacf5\ud3ec \ucee4\uc9c0\uba74 \ube44\uc911 \ud655\ub300"),
    ("normal", "neutral"): ("\ud3c9\uc628\u00b7\uc720\uc9c0", "\U0001f7e2",
        "\uc801\ub2f9\ud55c \uac00\uaca9, \uc801\ub2f9\ud55c \uc2ec\ub9ac\n"
        "\u2022 \uae30\uc874 \ud3ec\ud2b8\ud3f4\ub9ac\uc624 \uc720\uc9c0\n"
        "\u2022 \ud2b9\ubcc4\ud788 \uc0ac\uac70\ub098 \ud314 \uc774\uc720 \uc5c6\uc74c"),
    ("normal", "greed"): ("\uc695\uc2ec\uc790\uc81c", "\U0001f7e1",
        "\uac00\uaca9\uc740 OK\uc778\ub370 \ubd84\uc704\uae30 \uacfc\uc5f4\n"
        "\u2022 \ucd94\uaca9\ub9e4\uc218 \uc790\uc81c\n"
        "\u2022 \uc218\uc775 \uc77c\ubd80 \uc2e4\ud604 \uace0\ub824"),
    ("cheap", "fear"): ("\U0001f3af\uc778\uc0dd\ub9e4\uc218", "\U0001f7e2",
        "\uc2f8\uace0 \uacb8\uba39\uc74c = \ucd5c\uace0 \ud0c0\uc774\ubc0d\n"
        "\u2022 2009, 2020.3 \uac19\uc740 \uad6c\uac04\n"
        "\u2022 \uc6a9\uae30\ub0b4\uc11c \uc801\uadf9 \ub9e4\uc218"),
    ("cheap", "neutral"): ("\uc801\uadf9\ub9e4\uc218", "\U0001f7e2",
        "\uc2f8\uace0 \uc548\uc815 = \uc88b\uc740 \uc9c4\uc785\uc810\n"
        "\u2022 \uc7a5\uae30\ud22c\uc790 \uc2dc\uc791\ud558\uae30 \uc88b\uc740 \ub54c"),
    ("cheap", "greed"): ("\ud68c\ubcf5\ucd08\uae30", "\U0001f7e1",
        "\uc2f8\uc9c0\ub9cc \ud68c\ubcf5 \uc911\n"
        "\u2022 \uae30\uc874 \ud3ec\uc9c0\uc158 \uc720\uc9c0, \ucd94\uaca9 \uc790\uc81c"),
}


def _bucket(scores: list[int]) -> str:
    avg = sum(scores) / len(scores)
    if avg >= 3.8:
        return "expensive"
    if avg <= 2.2:
        return "cheap"
    return "normal"


def _sentiment_bucket(scores: list[int]) -> str:
    avg = sum(scores) / len(scores)
    if avg >= 3.8:
        return "greed"
    if avg <= 2.2:
        return "fear"
    return "neutral"


VALUATION_LABEL = {"expensive": "\U0001f4b8 비쌈", "normal": "\U0001f610 보통", "cheap": "\U0001f7e2 저렴"}
SENTIMENT_LABEL = {"fear": "\U0001f628 공포", "neutral": "\U0001f610 보통", "greed": "\U0001f911 탐욕"}


def diagnose(data: dict) -> dict:
    val_scores = []
    sent_scores = []
    indicators = {}

    if data.get("cape") is not None:
        s, e, d = interpret_cape(data["cape"])
        val_scores.append(s)
        indicators["cape"] = {"value": data["cape"], "fmt": f"{data['cape']:.1f}", "score": s, "emoji": e, "desc": d}

    if data.get("ecy") is not None:
        s, e, d = interpret_ecy(data["ecy"])
        val_scores.append(s)
        indicators["ecy"] = {"value": data["ecy"], "fmt": f"{data['ecy']:+.2f}%", "score": s, "emoji": e, "desc": d}

    if data.get("buffett") is not None:
        s, e, d = interpret_buffett(data["buffett"])
        val_scores.append(s)
        indicators["buffett"] = {"value": data["buffett"], "fmt": f"{data['buffett']:.0f}%", "score": s, "emoji": e, "desc": d}

    if data.get("yield_curve") is not None:
        s, e, d = interpret_yield_curve(data["yield_curve"])
        indicators["yield_curve"] = {"value": data["yield_curve"], "fmt": f"{data['yield_curve']:+.2f}%", "score": s, "emoji": e, "desc": d}

    if data.get("rate_10y") is not None:
        indicators["rate_10y"] = {"value": data["rate_10y"], "fmt": f"{data['rate_10y']:.2f}%"}

    if data.get("vix") is not None:
        s, e, d = interpret_vix(data["vix"])
        sent_scores.append(s)
        indicators["vix"] = {"value": data["vix"], "fmt": f"{data['vix']:.1f}", "score": s, "emoji": e, "desc": d}

    if data.get("cnn_fg") is not None:
        score_val, label = data["cnn_fg"]
        s, e, d = interpret_fg_stock(score_val)
        sent_scores.append(s)
        indicators["cnn_fg"] = {"value": score_val, "fmt": f"{score_val} ({label})", "score": s, "emoji": e, "desc": d}

    if data.get("crypto_fg") is not None:
        score_val, label = data["crypto_fg"]
        s, e, d = interpret_fg_crypto(score_val)
        sent_scores.append(s)
        indicators["crypto_fg"] = {"value": score_val, "fmt": f"{score_val} ({label})", "score": s, "emoji": e, "desc": d}

    val_bucket = _bucket(val_scores) if val_scores else "normal"
    sent_bucket = _sentiment_bucket(sent_scores) if sent_scores else "neutral"

    matrix_key = (val_bucket, sent_bucket)
    matrix_label, matrix_emoji, matrix_detail = MATRIX.get(matrix_key, ("판단 불가", "\u2753", "데이터 부족"))

    marks = calc_marks_temp(data)

    return {
        "indicators": indicators,
        "valuation": val_bucket,
        "sentiment": sent_bucket,
        "valuation_label": VALUATION_LABEL.get(val_bucket, "?"),
        "sentiment_label": SENTIMENT_LABEL.get(sent_bucket, "?"),
        "matrix_label": matrix_label,
        "matrix_emoji": matrix_emoji,
        "matrix_detail": matrix_detail,
        "marks": marks,
    }


def _norm(value: float, cold: float, hot: float) -> float:
    return max(0.0, min(100.0, (value - cold) / (hot - cold) * 100))


MARKS_LEVELS = [
    (20, "\u2744\ufe0f", "극단적 공포", "막스라면 \"지금 공격적으로 사라\""),
    (40, "\U0001f7e2", "차가움", "좋은 기회가 보이는 구간"),
    (60, "\U0001f7e1", "미지근", "평범, 선별적 투자"),
    (80, "\U0001f7e0", "\ub728\uac70\uc6c0", "\uc870\uc2ec! \ub9ac\uc2a4\ud06c \uc904\uc5ec\ub77c"),
    (100, "\U0001f534", "과열", "막스라면 \"방어 모드 전환\""),
]


def calc_marks_temp(data: dict) -> dict | None:
    components = {}

    if data.get("cape") is not None:
        components["CAPE"] = _norm(data["cape"], 10, 45)

    if data.get("vix") is not None:
        components["VIX"] = _norm(data["vix"], 45, 10)

    if data.get("cnn_fg") is not None:
        score_val = data["cnn_fg"][0] if isinstance(data["cnn_fg"], tuple) else data["cnn_fg"]
        components["F&G"] = float(score_val)

    if data.get("credit_spread") is not None:
        components["신용"] = _norm(data["credit_spread"], 10, 3)

    if not components:
        return None

    temp = sum(components.values()) / len(components)
    temp = round(temp)

    emoji = "\U0001f534"
    level = "과열"
    advice = "막스라면 \"방어 모드 전환\""
    for ceiling, e, lv, adv in MARKS_LEVELS:
        if temp <= ceiling:
            emoji, level, advice = e, lv, adv
            break

    bar_pos = max(0, min(14, round(temp / 100 * 14)))
    bar = "\u2744\ufe0f" + "\u2501" * bar_pos + "\u25cf" + "\u2501" * (14 - bar_pos) + "\U0001f525"

    return {
        "temp": temp,
        "emoji": emoji,
        "level": level,
        "advice": advice,
        "bar": bar,
        "components": components,
    }
