"""
Test DB connection pool exhaustion.
Gửi nhiều request song song để kiểm tra pool có bị cạn không.

Chạy: python tools/test_db_pool.py
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
EMAIL = os.getenv("TEST_EMAIL", "admin@naminc.dev")
PASSWORD = os.getenv("TEST_PASSWORD", "naminc")
CONCURRENT_STREAMS = 8  # Vượt pool_size=5


async def login(session):
    async with session.post(f"{API_URL}/auth/login", json={
        "email": EMAIL, "password": PASSWORD,
    }) as resp:
        data = await resp.json()
        if resp.status != 200:
            raise RuntimeError(f"Login thất bại: {data}")
        return data["access_token"]


async def stream_chat(session, token, idx):
    session_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    try:
        async with session.post(f"{API_URL}/chat", json={
            "session_id": session_id,
            "user_question": f"Sâu răng là gì? (concurrent {idx})",
            "chat_history": [],
        }, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                elapsed = time.perf_counter() - t0
                return f"🔴 stream-{idx}: HTTP {resp.status} after {elapsed:.1f}s"

            tokens = 0
            async for line in resp.content:
                decoded = line.decode().strip()
                if decoded.startswith("data: "):
                    try:
                        data = json.loads(decoded[6:])
                        if "token" in data:
                            tokens += 1
                        elif data.get("done"):
                            elapsed = time.perf_counter() - t0
                            return f"✓ stream-{idx}: {tokens} tokens, {elapsed:.1f}s"
                        elif data.get("error"):
                            elapsed = time.perf_counter() - t0
                            return f"🔴 stream-{idx}: ERROR '{data['error']}', {elapsed:.1f}s"
                    except json.JSONDecodeError:
                        pass
            elapsed = time.perf_counter() - t0
            return f"⚠ stream-{idx}: {tokens} tokens, no 'done', {elapsed:.1f}s"
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return f"🔴 stream-{idx}: FAILED after {elapsed:.1f}s — {e}"


async def main():
    print("=" * 70)
    print("  TEST DB CONNECTION POOL")
    print("=" * 70)
    print(f"  API: {API_URL}")
    print(f"  Concurrent streams: {CONCURRENT_STREAMS} (pool_size=5)")

    async with aiohttp.ClientSession() as session:
        print("\n[1] Đang login...")
        token = await login(session)
        print(f"    ✓ Login thành công")

        print(f"\n[2] Gửi {CONCURRENT_STREAMS} streams đồng thời...\n")
        t0 = time.perf_counter()
        tasks = [stream_chat(session, token, i) for i in range(CONCURRENT_STREAMS)]
        results = await asyncio.gather(*tasks)
        total = time.perf_counter() - t0

        for r in results:
            print(f"  {r}")

        failed = sum(1 for r in results if "🔴" in r)
        print(f"\n  Tổng thời gian: {total:.1f}s")
        print(f"  Thành công: {CONCURRENT_STREAMS - failed}/{CONCURRENT_STREAMS}")

        if failed > 0:
            print(f"  🔴 {failed} streams thất bại → DB pool có thể bị cạn!")
        else:
            print(f"  ✓ Tất cả streams thành công")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
