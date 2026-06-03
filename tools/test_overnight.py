"""
Health check liên tục + gửi chat request định kỳ.
Chạy qua đêm để phát hiện lúc nào app sập.

Chạy: python tools/test_overnight.py
Log sẽ ghi ra console và file tools/overnight_report.log
"""
import asyncio
import aiohttp
import json
import time
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = os.getenv("TEST_API_BASE", "http://127.0.0.1:8000")
API_URL = f"{API_BASE}/api"
EMAIL = os.getenv("TEST_EMAIL", "admin@naminc.dev")
PASSWORD = os.getenv("TEST_PASSWORD", "naminc")
CHECK_INTERVAL = 300       # 5 phút check 1 lần
CHAT_EVERY_N_CHECKS = 6   # Cứ 6 checks (30 phút) gửi 1 chat request
MAX_CONSECUTIVE_FAILS = 3  # Dừng sau N lần fail liên tiếp

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overnight_report.log")


def log(msg: str):
    """Log ra console và file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


async def check_health(session: aiohttp.ClientSession) -> tuple[bool, str]:
    try:
        async with session.get(
            f"{API_BASE}/health",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                return True, "OK"
            return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)


async def check_chat(session: aiohttp.ClientSession, token: str) -> tuple[bool, str]:
    session_id = str(uuid.uuid4())
    try:
        async with session.post(f"{API_URL}/chat", json={
            "session_id": session_id,
            "user_question": "Sâu răng là gì?",
            "chat_history": [],
        }, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}"

            tokens = 0
            t0 = time.perf_counter()
            async for line in resp.content:
                decoded = line.decode().strip()
                if decoded.startswith("data: "):
                    try:
                        data = json.loads(decoded[6:])
                        if "token" in data:
                            tokens += 1
                        elif data.get("done"):
                            elapsed = time.perf_counter() - t0
                            return True, f"{tokens} tokens, {elapsed:.1f}s"
                        elif data.get("error"):
                            return False, f"Stream error: {data['error']}"
                    except json.JSONDecodeError:
                        pass

            elapsed = time.perf_counter() - t0
            return False, f"{tokens} tokens, no done signal, {elapsed:.1f}s"
    except Exception as e:
        return False, str(e)


async def main():
    log("=" * 70)
    log("  OVERNIGHT HEALTH CHECK")
    log(f"  API: {API_BASE}")
    log(f"  Check interval: {CHECK_INTERVAL}s ({CHECK_INTERVAL // 60} min)")
    log(f"  Chat test every: {CHAT_EVERY_N_CHECKS} checks ({CHAT_EVERY_N_CHECKS * CHECK_INTERVAL // 60} min)")
    log("=" * 70)

    async with aiohttp.ClientSession() as session:
        # Login
        log("Đang login...")
        async with session.post(f"{API_URL}/auth/login", json={
            "email": EMAIL, "password": PASSWORD,
        }) as resp:
            data = await resp.json()
            if resp.status != 200:
                log(f"🔴 Login thất bại: {data}")
                return
            token = data["access_token"]
        log("✓ Login thành công")

        check_count = 0
        consecutive_fails = 0

        while True:
            check_count += 1

            # Health check
            health_ok, health_detail = await check_health(session)
            health_icon = "✓" if health_ok else "🔴"

            # Chat check mỗi N lần
            chat_status = ""
            if check_count % CHAT_EVERY_N_CHECKS == 0:
                chat_ok, chat_detail = await check_chat(session, token)
                chat_icon = "✓" if chat_ok else "🔴"
                chat_status = f" | Chat: {chat_icon} {chat_detail}"
                if not chat_ok:
                    consecutive_fails += 1
                else:
                    consecutive_fails = 0

            hours_running = (check_count * CHECK_INTERVAL) / 3600
            log(f"#{check_count} ({hours_running:.1f}h) Health: {health_icon} {health_detail}{chat_status}")

            if not health_ok:
                consecutive_fails += 1
                log(f"  🔴🔴🔴 APP KHÔNG PHẢN HỒI sau {hours_running:.1f}h")

            if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                log(f"\n❌ {consecutive_fails} lỗi liên tiếp. APP ĐÃ SẬP. Dừng monitoring.")
                log(f"   Tổng thời gian hoạt động: ~{hours_running:.1f}h ({check_count} checks)")
                break

            await asyncio.sleep(CHECK_INTERVAL)

    log("=" * 70)
    log("  MONITORING KẾT THÚC")
    log(f"  Report file: {LOG_FILE}")
    log("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
