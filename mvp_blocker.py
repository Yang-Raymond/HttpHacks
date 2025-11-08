import argparse, asyncio, json, os, sys, time, ctypes, threading, urllib.parse, re, ipaddress
from http.server import BaseHTTPRequestHandler, HTTPServer

# Track if we enabled PAC
_pac_enabled = False

# Track if we enabled PAC
_pac_enabled = False

# ---------- Blocklist ----------
class DomainMatcher:
    def __init__(self, domains, blocked_ips=None):
        exact, suffixes = set(), []
        for d in domains or []:
            d = d.strip().lower().rstrip(".")
            if not d:
                continue
            if d.startswith("*."):
                suffixes.append("." + d[2:])
            else:
                exact.add(d)
                suffixes.append("." + d)
        self.exact, self.suffixes = exact, suffixes
        # IP/CIDR support
        self.ip_nets = []
        for ip in blocked_ips or []:
            try:
                self.ip_nets.append(ipaddress.ip_network(ip, strict=False))
            except Exception:
                # ignore invalid entries
                pass

    def is_blocked(self, host: str) -> tuple[bool, str]:
        """
        Returns (blocked?, rule) where rule describes why:
          - "exact:example.com"
          - "suffix:.example.com"
          - "ip:203.0.113.10/32"
          - "none"
        """
        h = host.lower().rstrip(".")
        # IP check first
        try:
            ip = ipaddress.ip_address(h)
            for net in self.ip_nets:
                if ip in net:
                    return True, f"ip:{net.with_prefixlen}"
            return False, "none"
        except ValueError:
            pass  # not an IP, continue with domain logic
        if h in self.exact:
            return True, f"exact:{h}"
        for s in self.suffixes:
            if h.endswith(s):
                return True, f"suffix:{s}"
        return False, "none"

# ---------- Logging ----------
class Logger:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    async def write(self, kind, host, port, decision, rule=""):
        line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {kind} {host}:{port} {decision} {rule}\n'
        # offload real file I/O to a thread so we don't block the event loop
        await asyncio.to_thread(self._append_line, line)

    def _append_line(self, line: str):
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
            body_b = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
            # --- No-cache headers so browsers re-fetch immediately ---
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(body_b)))
            self.end_headers()
            self.wfile.write(body_b)
            return
        elif self.path == "/healthz":
            body_b = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body_b)))
            self.end_headers()
            self.wfile.write(body_b)
            return
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *_): pass

def start_pac_server(port: int, proxy_port: int, socks_port:int):
    PacHandler.proxy_port = proxy_port
    PacHandler.socks_port = socks_port
    httpd = HTTPServer(("127.0.0.1", port), PacHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd

# ---------- HTTP/HTTPS (CONNECT) proxy ----------
class HttpProxy:
    def __init__(self, host, port, matcher: DomainMatcher, logger: Logger):
        self.host, self.port, self.matcher, self.logger = host, port, matcher, logger

    async def _write_resp(self, w, code, text):
        body = f"{code} {text}\n"
        resp = f"HTTP/1.1 {code} {text}\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        w.write(resp.encode())
        try:
            await w.drain()
        except Exception:
            pass
        try:
            w.close(); await w.wait_closed()
        except Exception:
            pass

    async def _pipe(self, r, w):
        try:
            while True:
                chunk = await asyncio.wait_for(r.read(65536), timeout=PIPE_IDLE_TIMEOUT)
                if not chunk:
                    break
                w.write(chunk)
                await asyncio.wait_for(w.drain(), timeout=PIPE_IDLE_TIMEOUT)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

    async def _tunnel(self, cr, cw, host, port):
        try:
            ur, uw = await safe_open(host, port)
        except asyncio.TimeoutError:
            await self._write_resp(cw, 504, "Gateway Timeout"); return
        except Exception:
            await self._write_resp(cw, 502, "Bad Gateway"); return
        # 200 CONNECT established
        try:
            cw.write(b"HTTP/1.1 200 Connection Established\r\nProxy-Agent: PyMVP\r\n\r\n")
            await asyncio.wait_for(cw.drain(), timeout=PIPE_IDLE_TIMEOUT)
        except Exception:
            try: uw.close(); await uw.wait_closed()
            except Exception: pass
            return
        try:
            await asyncio.wait_for(
                asyncio.gather(self._pipe(cr, uw), self._pipe(ur, cw)),
                timeout=PIPE_SESSION_TIMEOUT
            )
        except asyncio.TimeoutError:
            pass
        finally:
            try: uw.close(); await uw.wait_closed()
            except Exception: pass
            try: cw.close(); await cw.wait_closed()
            except Exception: pass

    async def _forward_http(self, cr, cw, first_chunk, host, port):
        try:
            ur, uw = await safe_open(host, port)
        except asyncio.TimeoutError:
            await self._write_resp(cw, 504, "Gateway Timeout"); return
        except Exception:
            await self._write_resp(cw, 502, "Bad Gateway"); return
        try:
            uw.write(first_chunk)
            await asyncio.wait_for(uw.drain(), timeout=PIPE_IDLE_TIMEOUT)
            await asyncio.wait_for(
                asyncio.gather(self._pipe(ur, cw), self._pipe(cr, uw)),
                timeout=PIPE_SESSION_TIMEOUT
            )
        except asyncio.TimeoutError:
            pass
        finally:
            try: uw.close(); await uw.wait_closed()
            except Exception: pass
            try: cw.close(); await cw.wait_closed()
            except Exception: pass

    async def handle(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
        try:
            data = await asyncio.wait_for(r.readuntil(b"\r\n\r\n"), timeout=HEADER_TIMEOUT)
            if len(data) > MAX_HEADER_BYTES:
                await self._write_resp(w, 413, "Header Too Large"); return
        except asyncio.IncompleteReadError:
            try: w.close()
            except Exception: pass
            return
        except asyncio.TimeoutError:
            await self._write_resp(w, 408, "Request Timeout"); return

        header = data.decode("utf-8", "ignore")
        first = header.split("\r\n",1)[0]
        parts = first.split()
        if len(parts) < 2:
            await self._write_resp(w, 400, "Bad Request"); return
        method, target = parts[0].upper(), parts[1]

        if method == "CONNECT":
            try:
                host, port = parse_host_port(target)
            except ValueError:
                await self._write_resp(w, 400, "Malformed CONNECT"); return
            blocked, rule = self.matcher.is_blocked(host)
            decision = "BLOCK" if blocked else "ALLOW"
            await self.logger.write("CONNECT", host, port, decision, rule)
            if blocked:
                await self._write_resp(w, 403, "Forbidden"); return
            await self._tunnel(r, w, host, port); return

        # Absolute-URL HTTP via proxy
        if method in ("GET","POST","HEAD","PUT","DELETE","OPTIONS","PATCH"):
            u = urllib.parse.urlsplit(target)
            if not u.hostname:
                await self._write_resp(w, 400, "Proxy Requires Absolute-URI"); return
            host, port = u.hostname, u.port or (80 if u.scheme=="http" else 443)
            blocked, rule = self.matcher.is_blocked(host)
            decision = "BLOCK" if blocked else "ALLOW"
            await self.logger.write("HTTP", host, port, decision, rule)
            if blocked:
                await self._write_resp(w, 403, "Forbidden"); return
            await self._forward_http(r, w, data, host, port); return

        await self._write_resp(w, 405, "Method Not Allowed")

    async def run(self):
        # Bind; if fixed port fails, retry with 0 (any free port)
        try:
            srv = await asyncio.start_server(self.handle, self.host, self.port)
        except OSError:
            if self.port != 0:
                srv = await asyncio.start_server(self.handle, self.host, 0)
            else:
                raise
        actual_port = srv.sockets[0].getsockname()[1]
        self.port = actual_port
        print(f"[HTTP proxy] 127.0.0.1:{actual_port}")
        async with srv:
            await srv.serve_forever()

# ---------- Minimal SOCKS5 (TCP only) ----------
class Socks5Proxy:
    def __init__(self, host, port, matcher: DomainMatcher, logger: Logger):
        self.host, self.port, self.matcher, self.logger = host, port, matcher, logger

    async def handle(self, r, w):
        try:
            # greeting
            ver_n = await asyncio.wait_for(r.readexactly(2), timeout=HEADER_TIMEOUT)
            if ver_n[0] != 5:
                w.close(); return
            n = ver_n[1]
            _ = await asyncio.wait_for(r.readexactly(n), timeout=HEADER_TIMEOUT)  # methods
            w.write(b"\x05\x00"); await asyncio.wait_for(w.drain(), timeout=HEADER_TIMEOUT)  # no auth

            # request
            head = await asyncio.wait_for(r.readexactly(4), timeout=HEADER_TIMEOUT)  # ver, cmd, rsv, atyp
            if head[0] != 5 or head[1] not in (1,):  # only CONNECT
                w.write(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain(); w.close(); return

            atyp = head[3]
            if atyp == 1:  # IPv4
                addr = ".".join(str(x) for x in await asyncio.wait_for(r.readexactly(4), timeout=HEADER_TIMEOUT))
                host = addr
            elif atyp == 3:  # domain
                ln = (await asyncio.wait_for(r.readexactly(1), timeout=HEADER_TIMEOUT))[0]
                host = (await asyncio.wait_for(r.readexactly(ln), timeout=HEADER_TIMEOUT)).decode()
            elif atyp == 4:  # IPv6
                raw = await asyncio.wait_for(r.readexactly(16), timeout=HEADER_TIMEOUT)
                host = str(ipaddress.IPv6Address(raw))
            else:
                w.close(); return
            port = int.from_bytes(await asyncio.wait_for(r.readexactly(2), timeout=HEADER_TIMEOUT), "big")

            blocked, rule = self.matcher.is_blocked(host)
            decision = "BLOCK" if blocked else "ALLOW"
            await self.logger.write("SOCKS5", host, port, decision, rule)
            if blocked:
                w.write(b"\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain(); w.close(); return

            try:
                ur, uw = await io.open_connection(host, port)
            except:
                w.write(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain(); w.close(); return

            # success reply (bind address zeroed is acceptable; clients rarely rely on it)
            w.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00"); await w.drain()

            async def pipe(a, b):
                try:
                    while True:
                        chunk = await asyncio.wait_for(a.read(65536), timeout=PIPE_IDLE_TIMEOUT)
                        if not chunk: break
                        b.write(chunk); await asyncio.wait_for(b.drain(), timeout=PIPE_IDLE_TIMEOUT)
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass

            await asyncio.wait_for(asyncio.gather(pipe(r, uw), pipe(ur, w)), timeout=PIPE_SESSION_TIMEOUT)
            try: uw.close(); await uw.wait_closed()
            except Exception: pass
            try: w.close(); await w.wait_closed()
            except Exception: pass
        except Exception:
            try: w.close()
            except Exception: pass

    async def run(self):
        try:
            srv = await asyncio.start_server(self.handle, self.host, self.port)
        except OSError:
            if self.port != 0:
                srv = await asyncio.start_server(self.handle, self.host, 0)
            else:
                raise
        actual_port = srv.sockets[0].getsockname()[1]
        self.port = actual_port
        print(f"[SOCKS5]     127.0.0.1:{actual_port}")
        async with srv:
            await srv.serve_forever()

# ---------- Windows per-user PAC toggle (HKCU) ----------
def _wininet_refresh():
    # tell WinInet to re-read settings immediately
    INTERNET_OPTION_SETTINGS_CHANGED = 39
    INTERNET_OPTION_REFRESH = 37
    ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
    ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)

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

# ---------- CLI helpers ----------
def load_blocklist(path):
    """
    Accepts either:
      {"blocked": ["*.youtube.com", "example.com"]}  (legacy)
      {"blocked_domains": [...], "blocked_ips": ["203.0.113.0/24", "198.51.100.10"]} (extended)
    """
    if not path or not os.path.exists(path):
        return {"blocked_domains": ["*.steamcommunity.com", "*.steampowered.com", "login.example", "*.tracker.test"],
                "blocked_ips": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "blocked" in data and "blocked_domains" not in data:
        data = {"blocked_domains": data.get("blocked", []), "blocked_ips": []}
    data.setdefault("blocked_domains", [])
    data.setdefault("blocked_ips", [])
    return data

async def main_async(args):
    bl = load_blocklist(args.blocklist)
    matcher = DomainMatcher(bl.get("blocked_domains"), blocked_ips=bl.get("blocked_ips"))
    logger = Logger(args.log)

    # Start proxies first so we know actual bound ports (0 means "choose any free port")
    http = HttpProxy("127.0.0.1", args.proxy_port, matcher, logger)
    socks = Socks5Proxy("127.0.0.1", args.socks_port, matcher, logger)
    
    print("\n[INFO] Press Ctrl+C to stop")
    print("[INFO] Blocking is active\n")
    
    await asyncio.gather(http.run(), socks.run())

def main():
    global _pac_enabled
    p = argparse.ArgumentParser("MVP Domain Blocker (proxy+PAC, Python)")
    p.add_argument("--proxy-port", type=int, default=3128, help="0 = auto-pick free port")
    p.add_argument("--socks-port", type=int, default=1080, help="0 = auto-pick free port")
    p.add_argument("--pac-port",   type=int, default=18080, help="0 = auto-pick free port")
    p.add_argument("--enable-pac", action="store_true", help="(Windows) set user PAC on start")
    p.add_argument("--disable-pac", action="store_true", help="(Windows) clear user PAC then exit")
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