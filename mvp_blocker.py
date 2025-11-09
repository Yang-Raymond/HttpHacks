import argparse, asyncio, json, os, sys, time, ctypes, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

# Track if we enabled PAC
_pac_enabled = False

# ---------- Blocklist ----------
class DomainMatcher:
    def __init__(self, blocked_domains, unblocked_domains=None):
        unblocked_domains = unblocked_domains or []
        self.blocked_exact, self.blocked_suffixes = set(), []
        self.unblocked_exact, self.unblocked_suffixes = set(), []

        # Prepare blocked
        for d in blocked_domains:
            d = d.strip().lower().rstrip(".")
            if not d:
                continue
            if d.startswith("*."):
                self.blocked_suffixes.append("." + d[2:])
            else:
                self.blocked_exact.add(d)
                self.blocked_suffixes.append("." + d)

        # Prepare unblocked
        for d in unblocked_domains:
            d = d.strip().lower().rstrip(".")
            if not d:
                continue
            if d.startswith("*."):
                self.unblocked_suffixes.append("." + d[2:])
            else:
                self.unblocked_exact.add(d)
                self.unblocked_suffixes.append("." + d)

    def is_blocked(self, host: str) -> bool:
        h = host.lower().rstrip(".")

        # Explicitly allowed — if in unblocked list, never block
        if h in self.unblocked_exact or any(h.endswith(s) for s in self.unblocked_suffixes):
            return False

        # Explicitly blocked — only if found in blocked lists
        if h in self.blocked_exact or any(h.endswith(s) for s in self.blocked_suffixes):
            return True

        # Not listed anywhere → not blocked
        return False

# ---------- Logging ----------
class Logger:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._lock = asyncio.Lock()

    async def write(self, kind, host, port, decision):
        line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {kind} {host}:{port} {decision}\n'
        async with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line)

# ---------- PAC server ----------
PAC_TEMPLATE = """function FindProxyForURL(url, host) {
  if (isPlainHostName(host) ||
      shExpMatch(host, "localhost") ||
      isInNet(host, "10.0.0.0",  "255.0.0.0") ||
      isInNet(host, "172.16.0.0","255.240.0.0") ||
      isInNet(host, "192.168.0.0","255.255.0.0"))
    return "DIRECT";
  return "PROXY 127.0.0.1:%(proxy_port)s; SOCKS5 127.0.0.1:%(socks_port)s";
}"""

class PacHandler(BaseHTTPRequestHandler):
    proxy_port = 3128
    socks_port = 1080
    def do_GET(self):
        if self.path.startswith("/proxy.pac"):
            body = PAC_TEMPLATE % {"proxy_port": self.proxy_port, "socks_port": self.socks_port}
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *_): pass

def start_pac_server(port: int, proxy_port: int, socks_port:int):
    PacHandler.proxy_port = proxy_port
    PacHandler.socks_port = socks_port
    httpd = HTTPServer(("127.0.0.1", port), PacHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

# ---------- HTTP/HTTPS (CONNECT) proxy ----------
class HttpProxy:
    def __init__(self, host, port, matcher: DomainMatcher, logger: Logger):
        self.host, self.port, self.matcher, self.logger = host, port, matcher, logger

    async def _write_resp(self, w, code, text):
        body = f"{code} {text}\n"
        resp = f"HTTP/1.1 {code} {text}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n{body}"
        w.write(resp.encode()); await w.drain(); w.close(); 
        try: await w.wait_closed()
        except: pass

    async def _pipe(self, r, w):
        try:
            while True:
                chunk = await r.read(65536)
                if not chunk: break
                w.write(chunk); await w.drain()
        except: pass

    async def _tunnel(self, cr, cw, host, port):
        try:
            ur, uw = await asyncio.open_connection(host, port)
        except:
            await self._write_resp(cw, 502, "Bad Gateway"); return
        cw.write(b"HTTP/1.1 200 Connection Established\r\nProxy-Agent: PyMVP\r\n\r\n"); await cw.drain()
        try:
            await asyncio.gather(self._pipe(cr, uw), self._pipe(ur, cw))
        finally:
            uw.close(); 
            try: await uw.wait_closed()
            except: pass
            cw.close(); 
            try: await cw.wait_closed()
            except: pass

    async def _forward_http(self, cr, cw, first_chunk, host, port):
        try:
            ur, uw = await asyncio.open_connection(host, port)
        except:
            await self._write_resp(cw, 502, "Bad Gateway"); return
        try:
            uw.write(first_chunk); await uw.drain()
            await asyncio.gather(self._pipe(ur, cw), self._pipe(cr, uw))
        finally:
            uw.close(); 
            try: await uw.wait_closed()
            except: pass
            cw.close(); 
            try: await cw.wait_closed()
            except: pass

    async def handle(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
        try:
            data = await r.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError:
            w.close(); return
        header = data.decode("utf-8", "ignore")
        first = header.split("\r\n",1)[0]
        parts = first.split()
        if len(parts) < 2: 
            await self._write_resp(w, 400, "Bad Request"); return
        method, target = parts[0].upper(), parts[1]

        if method == "CONNECT":
            host, port = target.split(":")[0], int(target.split(":")[1])
            decision = "BLOCK" if self.matcher.is_blocked(host) else "ALLOW"
            await self.logger.write("CONNECT", host, port, decision)
            if decision == "BLOCK":
                await self._write_resp(w, 403, "Forbidden"); return
            await self._tunnel(r, w, host, port); return

        # Absolute-URL HTTP via proxy
        if method in ("GET","POST","HEAD","PUT","DELETE","OPTIONS","PATCH"):
            u = urllib.parse.urlsplit(target)
            if not u.hostname:
                await self._write_resp(w, 400, "Proxy Requires Absolute-URI"); return
            host, port = u.hostname, u.port or (80 if u.scheme=="http" else 443)
            decision = "BLOCK" if self.matcher.is_blocked(host) else "ALLOW"
            await self.logger.write("HTTP", host, port, decision)
            if decision == "BLOCK":
                await self._write_resp(w, 403, "Forbidden"); return
            await self._forward_http(r, w, data, host, port); return

        await self._write_resp(w, 405, "Method Not Allowed")

    async def run(self):
        srv = await asyncio.start_server(self.handle, self.host, self.port)
        print(f"[HTTP proxy] 127.0.0.1:{self.port}")
        async with srv: await srv.serve_forever()

# ---------- Minimal SOCKS5 (TCP only) ----------
class Socks5Proxy:
    def __init__(self, host, port, matcher: DomainMatcher, logger: Logger):
        self.host, self.port, self.matcher, self.logger = host, port, matcher, logger

    async def handle(self, r, w):
        try:
            # greeting
            ver_n = await r.readexactly(2)
            if ver_n[0] != 5: w.close(); return
            n = ver_n[1]
            _ = await r.readexactly(n)  # methods
            w.write(b"\x05\x00"); await w.drain()  # no auth

            # request
            head = await r.readexactly(4)  # ver, cmd, rsv, atyp
            if head[0] != 5 or head[1] not in (1,):  # only CONNECT
                w.write(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain(); w.close(); return

            atyp = head[3]
            if atyp == 1:  # IPv4
                addr = ".".join(str(x) for x in await r.readexactly(4))
                host = addr
            elif atyp == 3:  # domain
                ln = (await r.readexactly(1))[0]
                host = (await r.readexactly(ln)).decode()
            elif atyp == 4:  # IPv6
                raw = await r.readexactly(16)
                import ipaddress; host = str(ipaddress.IPv6Address(raw))
            else:
                w.close(); return
            port = int.from_bytes(await r.readexactly(2), "big")

            decision = "BLOCK" if self.matcher.is_blocked(host) else "ALLOW"
            await self.logger.write("SOCKS5", host, port, decision)
            if decision == "BLOCK":
                w.write(b"\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain(); w.close(); return

            try:
                ur, uw = await asyncio.open_connection(host, port)
            except:
                w.write(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain(); w.close(); return
            # success reply
            w.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain()

            async def pipe(a, b):
                try:
                    while True:
                        chunk = await a.read(65536)
                        if not chunk: break
                        b.write(chunk); await b.drain()
                except: pass

            await asyncio.gather(pipe(r, uw), pipe(ur, w))
            uw.close(); 
            try: await uw.wait_closed()
            except: pass
            w.close(); 
            try: await w.wait_closed()
            except: pass
        except:
            try: w.close()
            except: pass

    async def run(self):
        srv = await asyncio.start_server(self.handle, self.host, self.port)
        print(f"[SOCKS5]     127.0.0.1:{self.port}")
        async with srv: await srv.serve_forever()

# ---------- Windows per-user PAC toggle (HKCU) ----------
def set_user_pac(url: str):
    global _pac_enabled
    if sys.platform != "win32": 
        print("[INFO] PAC toggle only on Windows."); return
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "AutoConfigURL", 0, winreg.REG_SZ, url)
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        print(f"[OK] Enabled per-user PAC: {url}")
        _pac_enabled = True
    except Exception as e:
        print(f"[WARN] Could not set PAC automatically: {e}")

def clear_user_pac():
    if sys.platform != "win32": return
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as k:
            try: 
                winreg.DeleteValue(k, "AutoConfigURL")
            except FileNotFoundError:
                pass
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        print(f"[OK] Disabled per-user PAC")
    except Exception as e:
        print(f"[WARN] Could not clear PAC automatically: {e}")

# ---------- CLI ----------
def load_blocklist(path):
    """
    Loads JSON blocklist with nested objects, e.g.:
    {
      "blocked": {
        "YouTube": ["*.youtube.com", "youtu.be"],
        "TikTok": ["*.tiktok.com"]
      },
      "unblocked": {
        "Meta": ["*.facebook.com", "*.instagram.com"]
      }
    }

    Returns two flattened lists: (blocked_domains, unblocked_domains)
    """
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Blocklist file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    blocked_domains = []
    unblocked_domains = []

    # Flatten blocked lists
    for group in data.get("blocked", {}).values():
        blocked_domains.extend(group)

    # Flatten unblocked lists
    for group in data.get("unblocked", {}).values():
        unblocked_domains.extend(group)

    return blocked_domains, unblocked_domains

async def main_async(args):
    # Load flattened lists from blocklist.json
    blocked, unblocked = load_blocklist(args.blocklist)
    matcher = DomainMatcher(blocked, unblocked)
    logger = Logger(args.log)

    # PAC server
    start_pac_server(args.pac_port, args.proxy_port, args.socks_port)
    pac_url = f"http://127.0.0.1:{args.pac_port}/proxy.pac"
    print(f"[PAC]        {pac_url}")
    if args.enable_pac:
        set_user_pac(pac_url)
    if args.disable_pac:
        clear_user_pac()

    # Proxies
    http = HttpProxy("127.0.0.1", args.proxy_port, matcher, logger)
    socks = Socks5Proxy("127.0.0.1", args.socks_port, matcher, logger)
    
    print("\n[INFO] Press Ctrl+C to stop")
    print("[INFO] Blocking is active\n")
    
    await asyncio.gather(http.run(), socks.run())

def main():
    global _pac_enabled
    p = argparse.ArgumentParser("MVP Domain Blocker (proxy+PAC, Python)")
    p.add_argument("--proxy-port", type=int, default=3128)
    p.add_argument("--socks-port", type=int, default=1080)
    p.add_argument("--pac-port",   type=int, default=18080)
    p.add_argument("--enable-pac", action="store_true")
    p.add_argument("--disable-pac", action="store_true")
    p.add_argument("--blocklist",  type=str, default="blocklist.json")
    p.add_argument("--log",        type=str, default=os.path.join("logs","traffic.log"))
    args = p.parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[CLEANUP] Stopping...")
        if _pac_enabled:
            clear_user_pac()
            time.sleep(2)
            print("[CLEANUP] PAC removed, browsers should work now")

if __name__ == "__main__":
    main()