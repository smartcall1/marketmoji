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


def _draw_matrix(val: str, sent: str) -> list[str]:
    grid = {
        ("expensive", "fear"):    "\ud63c\uc870",
        ("expensive", "neutral"): "\uace0\uc810\uc8fc\uc758",
        ("expensive", "greed"):   "\U0001f6a8\ub3c4\ub9dd",
        ("normal",    "fear"):    "\uae30\ud68c\ud0d0\uc0c9",
        ("normal",    "neutral"): "\ud3c9\uc628",
        ("normal",    "greed"):   "\uc695\uc2ec\uc790\uc81c",
        ("cheap",     "fear"):    "\U0001f3af\uc778\uc0dd\ub9e4\uc218",
        ("cheap",     "neutral"): "\uc801\uadf9\ub9e4\uc218",
        ("cheap",     "greed"):   "\ud68c\ubcf5\ucd08\uae30",
    }
    rows = ["expensive", "normal", "cheap"]
    cols = ["fear", "neutral", "greed"]
    row_labels = {"expensive": "\U0001f4b8비쌈", "normal": "\U0001f610보통", "cheap": "\U0001f7e2저렴"}
    col_labels = {"fear": "\U0001f628\uacf5\ud3ec", "neutral": "\U0001f610\ubcf4\ud1b5", "greed": "\U0001f911\ud0d0\uc695"}

    lines = ["\u25a0 \ud604\uc7ac \uc704\uce58 \ub9e4\ud2b8\ub9ad\uc2a4"]
    lines.append(f"        {col_labels['fear']}  {col_labels['neutral']}  {col_labels['greed']}")

    for r in rows:
        cells = []
        for c in cols:
            cell = grid[(r, c)]
            if r == val and c == sent:
                cell = f"[{cell}]"
            cells.append(cell)
        line = f"  {row_labels[r]}  {'  '.join(cells)}"
        lines.append(line)

    return lines
