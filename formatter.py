from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def build_dashboard(diag: dict) -> str:
    now = datetime.now(KST).strftime("%m/%d %H:%M")
    ind = diag["indicators"]
    lines = [f"\U0001f4ca \uc2dc\uc7a5\uac74\uac15\uac80\uc9c4 \u2014 \ubbf8\uad6d \uac70\uc2dc\uacbd\uc81c/\uc8fc\uc2dd ({now})", ""]

    lines.append("\u25a0 \uac00\uaca9")
    for key in ("cape", "ecy", "buffett"):
        if key in ind:
            i = ind[key]
            name = {"cape": "CAPE", "ecy": "ECY", "buffett": "Buffett"}[key]
            lines.append(f"{name} {i['fmt']} {i['emoji']}{i['desc']}")

    if "concentration" in ind:
        lines.append("")
        lines.append("\u25a0 \uc9d1\uc911\ub3c4")
        i = ind["concentration"]
        lines.append(f"Big10 {i['fmt']} {i['emoji']}{i['desc']}")

    lines.append("")
    lines.append("\u25a0 \uacbd\uae30")
    if "yield_curve" in ind:
        i = ind["yield_curve"]
        lines.append(f"Yield Curve {i['fmt']} {i['emoji']}{i['desc']}")
    if "rate_10y" in ind:
        lines.append(f"10Y {ind['rate_10y']['fmt']}")

    lines.append("")
    lines.append("\u25a0 \uc2ec\ub9ac")
    if "vix" in ind:
        i = ind["vix"]
        lines.append(f"VIX {i['fmt']} {i['emoji']}{i['desc']}")
    if "cnn_fg" in ind:
        i = ind["cnn_fg"]
        lines.append(f"F&G\uc8fc\uc2dd {i['fmt']} {i['emoji']}{i['desc']}")
    if "crypto_fg" in ind:
        i = ind["crypto_fg"]
        lines.append(f"F&G\ucf54\uc778 {i['fmt']} {i['emoji']}{i['desc']}")

    marks = diag.get("marks")
    if marks:
        lines.append("")
        lines.append(f"\U0001f321\ufe0f \ub9c9\uc2a4 {marks['temp']}/100 {marks['emoji']}{marks['level']}")
        lines.append(marks["bar"])
        comp = " | ".join(f"{k}{v:.0f}" for k, v in marks["components"].items())
        lines.append(comp)
        lines.append(f"\U0001f4ac {marks['advice']}")

    lines.append("")
    lines.append("\u25a0 \uc9c4\ub2e8")
    v = diag["valuation_label"]
    s = diag["sentiment_label"]
    lines.append(f"{v} + {s}")
    lines.append(f"\u27a1\ufe0f {diag['matrix_emoji']}{diag['matrix_label']}")
    lines.append("")

    for detail_line in diag["matrix_detail"].split("\n"):
        lines.append(detail_line)

    lines.append("")
    lines.append("/guide \uc9c0\ud45c\ud574\uc11d\ubc95")

    return "\n".join(lines)


_COMBOS = [
    ("expensive", "fear",    "\U0001f4b8\U0001f628", "\ud63c\uc870\u00b7\ubd84\ud560\ub9e4\uc218"),
    ("expensive", "neutral", "\U0001f4b8\U0001f610", "\uace0\uc810\uc8fc\uc758"),
    ("expensive", "greed",   "\U0001f4b8\U0001f911", "\U0001f6a8\ub3c4\ub9dd\uccd0"),
    ("normal",    "fear",    "\U0001f610\U0001f628", "\uae30\ud68c\ud0d0\uc0c9"),
    ("normal",    "neutral", "\U0001f610\U0001f610", "\ud3c9\uc628"),
    ("normal",    "greed",   "\U0001f610\U0001f911", "\uc695\uc2ec\uc790\uc81c"),
    ("cheap",     "fear",    "\U0001f7e2\U0001f628", "\U0001f3af\uc778\uc0dd\ub9e4\uc218"),
    ("cheap",     "neutral", "\U0001f7e2\U0001f610", "\uc801\uadf9\ub9e4\uc218"),
    ("cheap",     "greed",   "\U0001f7e2\U0001f911", "\ud68c\ubcf5\ucd08\uae30"),
]


def _draw_compass(val: str, sent: str) -> list[str]:
    lines = ["\u25a0 \ub098\uce68\ubc18"]
    for v, s, icons, label in _COMBOS:
        marker = " \u2190\u2605" if v == val and s == sent else ""
        lines.append(f"{icons} {label}{marker}")
    return lines
