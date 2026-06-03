"""
Test SSE streaming leak.
Mô phỏng client disconnect giữa stream để kiểm tra resource leak.

Chạy: python tools/test_sse_leak.py
Yêu cầu: Backend đang chạy tại localhost:8000
"""
import asyncio
import aiohttp
import json
import time
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")

# ─── Config ───
EMAIL = os.getenv("TEST_EMAIL", "admin@naminc.dev")
PASSWORD = os.getenv("TEST_PASSWORD", "naminc")
NUM_DISCONNECTS = 10        # Số lần disconnect giữa stream
DISCONNECT_AFTER_TOKENS = 3 # Disconnect sau N tokens nhận được
NUM_NORMAL_AFTER = 3        # Số request bình thường sau đó


async def login(session: aiohttp.ClientSession) -> str:
    """Login và trả về JWT token."""
    async with session.post(f"{API_URL}/auth/login", json={
        "email": EMAIL, "password": PASSWORD,
    }) as resp:
        data = await resp.json()
        if resp.status != 200:
            raise RuntimeError(f"Login thất bại: {data}")
        return data["access_token"]


async def send_chat_and_disconnect(
    session: aiohttp.ClientSession,
    token: str,
    question: str,
    disconnect_after: int | None = None,
) -> dict:
    """
    Gửi chat request.
    Nếu disconnect_after != None: ngắt kết nối sau N tokens.
    Trả về dict với thông tin timing và token count.
    """
    session_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "session_id": session_id,
        "user_question": question,
        "chat_history": [],
    }

    t0 = time.perf_counter()
    token_count = 0
    got_done = False
    error = None

    try:
        async with session.post(
            f"{API_URL}/chat",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as resp:
            if resp.status != 200:
                return {"error": f"HTTP {resp.status}", "elapsed": 0}

            async for line in resp.content:
                decoded = line.decode("utf-8").strip()
                if not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:].strip()
                if not data_str:
                    continue

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if "token" in data:
                    token_count += 1
                    if disconnect_after and token_count >= disconnect_after:
                        # Simulate client disconnect
                        break
                elif data.get("done"):
                    got_done = True

    except asyncio.CancelledError:
        error = "CancelledError"
    except Exception as e:
        error = str(e)

    elapsed = time.perf_counter() - t0
    return {
        "tokens": token_count,
        "done": got_done,
        "elapsed": round(elapsed, 2),
        "disconnected": disconnect_after is not None and token_count >= disconnect_after,
        "error": error,
    }


async def main():
    print("=" * 70)
    print("  TEST SSE STREAMING LEAK")
    print("=" * 70)
    print(f"  API: {API_URL}")
    print(f"  Disconnect after: {DISCONNECT_AFTER_TOKENS} tokens")
    print(f"  Rounds: {NUM_DISCONNECTS} disconnect + {NUM_NORMAL_AFTER} normal")

    async with aiohttp.ClientSession() as session:
        # Login
        print("\n[1] Đang login...")
        token = await login(session)
        print(f"    ✓ Login thành công")

        # Phase 1: Disconnect giữa stream nhiều lần
        print(f"\n[2] Gửi {NUM_DISCONNECTS} request và disconnect giữa stream...")
        for i in range(NUM_DISCONNECTS):
            result = await send_chat_and_disconnect(
                session, token,
                f"Sâu răng là gì? (test {i+1})",
                disconnect_after=DISCONNECT_AFTER_TOKENS,
            )
            status = "🔴 DISCONNECT" if result.get("disconnected") else "✓"
            print(f"    [{i+1}/{NUM_DISCONNECTS}] {status} | "
                  f"tokens={result['tokens']} | {result['elapsed']}s | "
                  f"error={result.get('error')}")
            await asyncio.sleep(1)

        # Phase 2: Request bình thường để kiểm tra app còn respond không
        print(f"\n[3] Gửi {NUM_NORMAL_AFTER} request bình thường sau đó...")
        for i in range(NUM_NORMAL_AFTER):
            t0 = time.perf_counter()
            result = await send_chat_and_disconnect(
                session, token,
                f"Viêm nướu là gì? (verify {i+1})",
                disconnect_after=None,  # Không disconnect
            )
            elapsed = time.perf_counter() - t0
            status = "✓ DONE" if result.get("done") else "🔴 FAILED"
            print(f"    [{i+1}/{NUM_NORMAL_AFTER}] {status} | "
                  f"tokens={result['tokens']} | {round(elapsed, 2)}s | "
                  f"error={result.get('error')}")
            await asyncio.sleep(2)

    print("\n" + "=" * 70)
    print("  KẾT LUẬN:")
    print("  - Nếu Phase 3 bị timeout/fail → Có generator/connection leak")
    print("  - Nếu Phase 3 OK → Leak đã được fix hoặc cần nhiều request hơn")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
