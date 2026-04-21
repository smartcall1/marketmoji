from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def build_dashboard(diag: dict) -> str:
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    ind = diag["indicators"]
    lines = [f"\U0001f4ca \uc2dc\uc7a5 \uac74\uac15\uac80\uc9c4 ({now})", ""]

    lines.append("\u25a0 \uc9c0\uae08 \ube44\uc2fc\uac00?")
    if "cape" in ind:
        i = ind["cape"]
        lines.append(f"  CAPE  {i['fmt']}  {i['emoji']} {i['desc']}")
    if "ecy" in ind:
        i = ind["ecy"]
        lines.append(f"  ECY  {i['fmt']}  {i['emoji']} {i['desc']}")
    if "buffett" in ind:
        i = ind["buffett"]
        lines.append(f"  Buffett  {i['fmt']}  {i['emoji']} {i['desc']}")

    lines.append("")
    lines.append("\u25a0 \uacbd\uae30\uce68\uccb4 \uc624\ub098?")
    if "yield_curve" in ind:
        i = ind["yield_curve"]
        lines.append(f"  Yield Curve  {i['fmt']}  {i['emoji']} {i['desc']}")
    if "rate_10y" in ind:
        i = ind["rate_10y"]
        lines.append(f"  10Y \uae08\ub9ac  {i['fmt']}")

    lines.append("")
    lines.append("\u25a0 \uc0ac\ub78c\ub4e4 \uc2ec\ub9ac")
    if "vix" in ind:
        i = ind["vix"]
        lines.append(f"  VIX  {i['fmt']}  {i['emoji']} {i['desc']}")
    if "cnn_fg" in ind:
        i = ind["cnn_fg"]
        lines.append(f"  F&G(\uc8fc\uc2dd)  {i['fmt']}  {i['emoji']} {i['desc']}")
    if "crypto_fg" in ind:
        i = ind["crypto_fg"]
        lines.append(f"  F&G(\ucf54\uc778)  {i['fmt']}  {i['emoji']} {i['desc']}")

    lines.append("")
    lines.append("\u25a0 \uc885\ud569 \uc9c4\ub2e8")
    lines.append("")

    v = diag["valuation_label"]
    s = diag["sentiment_label"]
    lines.append(f"\U0001f4cd \ud604\uc7ac \uc0c1\ud0dc: {v} + {s}")
    lines.append(f"\u27a1\ufe0f  {diag['matrix_emoji']} {diag['matrix_label']}")
    lines.append("")

    lines.append(f"\U0001f4a1 \uc774 \uc870\ud569\uc774 \uc758\ubbf8\ud558\ub294 \uac83")
    for detail_line in diag["matrix_detail"].split("\n"):
        lines.append(f"  {detail_line}")

    lines.append("")
    matrix_lines = _draw_matrix(diag["valuation"], diag["sentiment"])
    lines.extend(matrix_lines)

    lines.append("")
    lines.append("\U0001f50d /guide \ub85c \uac01 \uc9c0\ud45c \ud574\uc11d\ubc95 \ud655\uc778")

    return "\n".join(lines)


_COMBOS = [
    ("expensive", "fear",    "\U0001f4b8+\U0001f628", "혼조 \u00b7 분할매수"),
    ("expensive", "neutral", "\U0001f4b8+\U0001f610", "고점주의"),
    ("expensive", "greed",   "\U0001f4b8+\U0001f911", "\U0001f6a8 도망쳐"),
    ("normal",    "fear",    "\U0001f610+\U0001f628", "기회탐색"),
    ("normal",    "neutral", "\U0001f610+\U0001f610", "평온 \u00b7 유지"),
    ("normal",    "greed",   "\U0001f610+\U0001f911", "욕심자제"),
    ("cheap",     "fear",    "\U0001f7e2+\U0001f628", "\U0001f3af 인생매수"),
    ("cheap",     "neutral", "\U0001f7e2+\U0001f610", "적극매수"),
    ("cheap",     "greed",   "\U0001f7e2+\U0001f911", "회복초기"),
]


def _draw_matrix(val: str, sent: str) -> list[str]:
    lines = ["\u25a0 \uc2dc\uc7a5 \ub098\uce68\ubc18 (\uac00\uaca9+\uc2ec\ub9ac \uc870\ud569\ud45c)"]
    for v, s, icons, label in _COMBOS:
        marker = " \u2190 \u2605\uc9c0\uae08 \uc5ec\uae30" if v == val and s == sent else ""
        lines.append(f"  {icons} {label}{marker}")
    return lines
