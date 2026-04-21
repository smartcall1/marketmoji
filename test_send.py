import asyncio
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from fetchers import fetch_all
from interpreter import diagnose
from formatter import build_dashboard


async def main():
    print("[1/4] 봇 토큰 확인...")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe")
        info = r.json()
        if not info.get("ok"):
            print(f"  FAIL: {info}")
            return
        bot_name = info["result"]["username"]
        print(f"  OK: @{bot_name}")

    print("[2/4] 데이터 수집 중...")
    data = await fetch_all()
    ok = {k: v for k, v in data.items() if v is not None}
    fail = {k: v for k, v in data.items() if v is None}
    print(f"  OK: {list(ok.keys())}")
    if fail:
        print(f"  FAIL: {list(fail.keys())}")

    print("[3/4] 대시보드 생성...")
    diag = diagnose(data)
    msg = build_dashboard(diag)
    print(f"  OK: {len(msg)} chars")

    print(f"[4/4] 텔레그램 전송 (chat_id={TELEGRAM_CHAT_ID})...")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        )
        result = r.json()
        if result.get("ok"):
            print("  SUCCESS! 텔레그램 확인하세요.")
        else:
            print(f"  FAIL: {result}")


if __name__ == "__main__":
    asyncio.run(main())
