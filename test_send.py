"""Daily alert 미리보기 — 대시보드 + Top Signal 2개 메시지 전송."""
import asyncio
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from fetchers import fetch_all
from interpreter import diagnose
from formatter import build_dashboard
from top_signal import fetch_top_signals, format_top_signal


async def main():
    print("[1/5] 봇 토큰 확인...")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe")
        info = r.json()
        if not info.get("ok"):
            print(f"  FAIL: {info}")
            return
        bot_name = info["result"]["username"]
        print(f"  OK: @{bot_name}")

    print("[2/5] 거시경제 데이터 수집 중...")
    data = await fetch_all()
    ok = {k: v for k, v in data.items() if v is not None}
    fail = {k: v for k, v in data.items() if v is None}
    print(f"  OK: {list(ok.keys())}")
    if fail:
        print(f"  FAIL: {list(fail.keys())}")

    print("[3/5] Top Signal 수집 중...")
    sig_data = await fetch_top_signals()
    online = sig_data["online"]
    hits = sig_data["hits"]
    print(f"  OK: {online}/12 지표 온라인, {hits} HIT")

    print("[4/5] 메시지 생성...")
    diag = diagnose(data)
    msg1 = build_dashboard(diag)
    msg2 = format_top_signal(sig_data)
    print(f"  대시보드: {len(msg1)} chars")
    print(f"  Top Signal: {len(msg2)} chars")

    print(f"[5/5] 텔레그램 전송 (chat_id={TELEGRAM_CHAT_ID})...")
    async with httpx.AsyncClient(timeout=15) as c:
        r1 = await c.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg1},
        )
        r2 = await c.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg2},
        )
        if r1.json().get("ok") and r2.json().get("ok"):
            print("  ✅ 2개 메시지 전송 성공! 텔레그램 확인하세요.")
        else:
            if not r1.json().get("ok"):
                print(f"  FAIL (대시보드): {r1.json()}")
            if not r2.json().get("ok"):
                print(f"  FAIL (Top Signal): {r2.json()}")


if __name__ == "__main__":
    asyncio.run(main())
