"""
Collapse Signal — KB증권 이은택 위원 「Gravity Rules」(2026-05-29) 보고서 기반
AI 버블 붕괴 3가지 핵심 시그널 추적 + 추세 판정.

근거: https://blog.naver.com/onejejuwave/224300807261

이은택 위원의 결론(원문):
  ① 미국 10년물 국채금리를 주목한다
  ② 10~20년간 보지 못했던 '역사적 고점'을 돌파하는 시기를 주목한다
     → 5.0~5.3% 추세적 돌파 (2007년 이후 미경험 수준)
  ③ '절망(이제는 되돌릴 수 없을 거야)'이 가세할 인플레가 있어야 한다
     → Core CPI ≥ 3.0%
     → 주거비 제외 sticky CPI ≥ 3.4%

추세 판정 (블로그 본문 "추세적, 돌이킬 수 없는" 강조 반영):
  - 10Y: 최근 20영업일 중 15일 이상 임계 위 → TRENDING_UP
  - CPI: 최근 3개 데이터 포인트 연속 임계 위 → TRENDING_UP

추세 상태별 점화 가중치:
  TRENDING_UP   = 본격 점화 (블로그가 말한 "추세적")
  SPIKED        = 단발 침투 (현재 임계 이상이나 추세 미확정)
  APPROACHING   = WARN 이상이며 추세 상승 중
  STABLE        = 안정
"""

import asyncio
from datetime import datetime, timezone, timedelta

from fetchers import (
    fetch_sticky_core_cpi,
    fetch_10y_history,
    fetch_core_cpi_yoy_history,
    fetch_sticky_ex_shelter_history,
)

KST = timezone(timedelta(hours=9))


SIGNALS = [
    {
        "id": "ust10y",
        "name": "미국 10Y 국채금리",
        "warn": 5.0,
        "trigger": 5.3,
        "unit": "%",
        "trend_window": 20,       # 최근 20영업일
        "trend_hits_needed": 15,  # 15일 이상
        "note": "20년래 고점(2007년 이후 미경험) 돌파 = '되돌릴 수 없는' 긴축 신호",
    },
    {
        "id": "core_cpi",
        "name": "Core CPI YoY",
        "warn": 2.7,
        "trigger": 3.0,
        "unit": "%",
        "trend_window": 3,        # 최근 3개월
        "trend_hits_needed": 3,   # 3개월 연속
        "note": "3.0% 상회 = 인플레이션 절망감 점화 (2000년 닷컴버블 패턴)",
    },
    {
        "id": "sticky_ex_shelter",
        "name": "Sticky CPI ex-주거비 YoY",
        "warn": 3.1,
        "trigger": 3.4,
        "unit": "%",
        "trend_window": 3,
        "trend_hits_needed": 3,
        "note": "주거비 제외 sticky 3.4% 상회 = 끈적한 인플레의 본격 재점화",
    },
]


def _slope_up(values: list[float], min_points: int = 3) -> bool:
    """단순 상승 추세: 첫값 < 마지막값, 최저점 < 최고점."""
    if len(values) < min_points:
        return False
    return values[-1] > values[0]


def _classify(value: float | None, history: list[float] | None, sig: dict) -> tuple[str, str, str]:
    """(상태, 추세, 이모지) 반환."""
    warn, trigger = sig["warn"], sig["trigger"]
    window = sig["trend_window"]
    hits_needed = sig["trend_hits_needed"]

    if value is None:
        return "DATA", "—", "⬜"

    # 추세 판정용 최근 N개
    recent = history[-window:] if history else []
    hits_above_trigger = sum(1 for v in recent if v >= trigger)
    rising = _slope_up(recent)

    # 점화 상태
    if value >= trigger:
        if hits_above_trigger >= hits_needed:
            state, trend, emoji = "TRIGGER", "TRENDING", "🚨"
        else:
            state, trend, emoji = "SPIKED", "SPIKE", "🟥"
    elif value >= warn:
        if rising:
            state, trend, emoji = "WARN", "RISING", "🟠"
        else:
            state, trend, emoji = "WARN", "FLAT", "🟡"
    else:
        if rising and value >= warn * 0.95:
            state, trend, emoji = "WATCH", "RISING", "🟡"
        else:
            state, trend, emoji = "SAFE", "STABLE", "🟢"

    return state, trend, emoji


TREND_LABEL = {
    "TRENDING": "🚨 진짜 점화 (계속 임계값 위)",
    "SPIKE": "🟥 일시 돌파 (한 번 찔러봄)",
    "RISING": "📈 임박 + 오르는 중",
    "FLAT": "🟡 임박 (횡보)",
    "STABLE": "✓ 안전",
    "—": "데이터 없음",
}


RISK_LABEL_KO = {
    "SAFE":        "🟢 평온",
    "WATCH-LITE":  "🟡 경계선 진입",
    "WATCH":       "🟠 주시 단계",
    "CAUTION":     "🔴 위험 단계",
    "DANGER":      "🚨 매우 위험",
    "COLLAPSE":    "💀 붕괴 패턴",
}


async def fetch_collapse_signals() -> dict:
    """3가지 붕괴 시그널 + 추세 판정. history 한 번만 호출하고 마지막 값을 latest로 사용."""

    ust10y_hist_t = asyncio.create_task(fetch_10y_history(30))
    core_cpi_hist_t = asyncio.create_task(fetch_core_cpi_yoy_history(6))
    sticky_core_t = asyncio.create_task(fetch_sticky_core_cpi())
    sticky_ex_hist_t = asyncio.create_task(fetch_sticky_ex_shelter_history(6))

    ust10y_hist = await ust10y_hist_t
    core_cpi_hist = await core_cpi_hist_t
    sticky_core = await sticky_core_t
    sticky_ex_hist = await sticky_ex_hist_t

    def _split(h):
        """tuple history → ([values], latest_date) / 단순 list → (list, None)."""
        if not h:
            return None, None
        if isinstance(h[0], tuple):
            return [v for _, v in h], h[-1][0]
        return list(h), None

    ust10y_vals, _ = _split(ust10y_hist)
    core_cpi_vals, core_cpi_date = _split(core_cpi_hist)
    sticky_ex_vals, sticky_ex_date = _split(sticky_ex_hist)

    raw = {
        "ust10y":            {"val": ust10y_vals[-1] if ust10y_vals else None,
                              "date": None, "hist": ust10y_vals},
        "core_cpi":          {"val": core_cpi_vals[-1] if core_cpi_vals else None,
                              "date": core_cpi_date, "hist": core_cpi_vals},
        "sticky_ex_shelter": {"val": sticky_ex_vals[-1] if sticky_ex_vals else None,
                              "date": sticky_ex_date, "hist": sticky_ex_vals},
    }

    results = []
    triggered = 0
    spiked = 0
    warned = 0
    online = 0

    for sig in SIGNALS:
        r = raw.get(sig["id"], {})
        val = r.get("val")
        hist = r.get("hist")
        state, trend, emoji = _classify(val, hist, sig)

        if val is not None:
            online += 1
        if state == "TRIGGER":
            triggered += 1
        elif state == "SPIKED":
            spiked += 1
        elif state == "WARN":
            warned += 1

        results.append({
            **sig,
            "value": val,
            "date": r.get("date"),
            "history": hist,
            "state": state,
            "trend": trend,
            "trend_label": TREND_LABEL.get(trend, trend),
            "emoji": emoji,
        })

    extra = {
        "sticky_core": sticky_core,
    }

    # 종합 리스크 — 진짜 점화(TRIGGER)에 큰 가중치
    if triggered >= 2:
        risk_level, risk_emoji = "COLLAPSE", "💀"
        verdict = "2개 축이 진짜 점화됐소. 1929·2000년 버블 붕괴 패턴 재현."
    elif triggered == 1 and spiked >= 1:
        risk_level, risk_emoji = "DANGER", "🚨"
        verdict = "한 축 점화 + 다른 축 일시 돌파. 두 번째 점화 임박."
    elif triggered == 1:
        risk_level, risk_emoji = "CAUTION", "🔴"
        verdict = "한 축 점화됐소. 나머지 축도 추적 필수."
    elif spiked >= 1:
        risk_level, risk_emoji = "WATCH", "🟠"
        verdict = "임계값 한 번 찔렀소. 계속 위에 머물면 진짜 점화."
    elif warned >= 2:
        risk_level, risk_emoji = "WATCH", "🟠"
        verdict = "두 개 이상 축이 임박 단계. 인플레 재점화 가능성."
    elif warned == 1:
        risk_level, risk_emoji = "WATCH-LITE", "🟡"
        verdict = "한 축이 트리거 직전. 임계값 추적 시작하시오."
    else:
        risk_level, risk_emoji = "SAFE", "🟢"
        verdict = "강세장 지속. AI 랠리는 아직 살아있소이다."

    return {
        "signals": results,
        "triggered": triggered,
        "spiked": spiked,
        "warned": warned,
        "online": online,
        "total": len(SIGNALS),
        "risk_level": risk_level,
        "risk_emoji": risk_emoji,
        "verdict": verdict,
        "extra": extra,
        "timestamp": datetime.now(KST).strftime("%m/%d %H:%M"),
    }


def _mini_sparkline(values: list[float] | None, n: int = 8) -> str:
    """간단 스파크라인 (▁▂▃▄▅▆▇█)."""
    if not values or len(values) < 2:
        return ""
    vals = values[-n:]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return "▄" * len(vals)
    bars = "▁▂▃▄▅▆▇█"
    out = []
    for v in vals:
        idx = int((v - lo) / (hi - lo) * (len(bars) - 1))
        out.append(bars[idx])
    return "".join(out)


def format_collapse_signal(data: dict) -> str:
    lines = []
    lines.append(f"💥 붕괴 시그널 — KB 이은택 「Gravity Rules」 ({data['timestamp']})")
    lines.append("")
    risk_ko = RISK_LABEL_KO.get(data["risk_level"], f"{data['risk_emoji']}{data['risk_level']}")
    lines.append(f"■ 종합 위험도: {risk_ko}")
    lines.append(
        f"   진짜점화 {data['triggered']} · 일시돌파 {data['spiked']} · 임박 {data['warned']}  (3개 축 중)"
    )
    lines.append("")

    for sig in data["signals"]:
        val = sig["value"]
        val_str = f"{val:.2f}{sig['unit']}" if val is not None else "—"
        trigger_str = f"≥{sig['trigger']}{sig['unit']}"
        warn_str = f"≥{sig['warn']}{sig['unit']}"
        spark = _mini_sparkline(sig.get("history"))
        trend_window_label = (
            f"최근 20영업일 중 15일 이상"
            if sig["id"] == "ust10y"
            else f"최근 3개월 연속"
        )

        lines.append(f"{sig['emoji']} {sig['name']}")
        lines.append(f"   ↳ 상태: {sig['trend_label']}")
        lines.append(f"   현재값: {val_str}")
        lines.append(f"   기준: 임박 {warn_str} / 점화 {trigger_str}")
        if spark:
            lines.append(f"   추세: {spark}  ({trend_window_label} 점화로 인정)")
        lines.append(f"   💡 {sig['note']}")
        lines.append("")

    sc = data["extra"].get("sticky_core")
    if sc is not None:
        sc_val = sc[1] if isinstance(sc, tuple) else sc
        lines.append(f"※ 참조: Sticky Core CPI(주거비 포함) {sc_val:.2f}%")
        lines.append("")

    lines.append(f"💬 {data['verdict']}")
    lines.append("")
    lines.append("📖 용어 설명:")
    lines.append(" • 진짜 점화 = 임계값을 계속(추세적으로) 넘은 상태 → 위험 확정")
    lines.append(" • 일시 돌파 = 임계값을 한 번만 찔러본 상태 → 추세 확정 시 점화")
    lines.append(" • 임박     = 점화 직전 단계 → 추적 시작")
    lines.append("")
    lines.append("📖 3축이 모두 진짜 점화 = 1929·2000년 버블 붕괴 패턴")

    return "\n".join(lines)
