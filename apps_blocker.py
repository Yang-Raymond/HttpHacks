"""
apps_blocker.py — minimal cross-platform app blocker (psutil required)

Usage pattern (async):
    blocker = AppBlocker(
        patterns=["discord.exe", "steam*", "Spotify.exe", "LeagueClientUx*"],
        mode="strict",                # "polite" | "strict"
        grace_seconds=2.0,            # how long to wait before kill() in strict
        scan_interval=2.0,            # how often to scan processes
        logger=None,                  # optional: your Logger from the proxy script
        dry_run=False                 # True = log only, don't terminate
    )
    task = asyncio.create_task(blocker.run())
    ...
    task.cancel()
"""

from __future__ import annotations
import asyncio
import fnmatch
import os
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

try:
    import psutil  # type: ignore
except ImportError as e:
    raise SystemExit("apps_blocker.py requires `psutil`. pip install psutil") from e


@dataclass(frozen=True)
class _Rule:
    pattern: str
    lower: str

    def match_name(self, name: str) -> bool:
        # case-insensitive wildcard matching against process name and basename of exe
        return fnmatch.fnmatchcase(name.lower(), self.lower)

    def __repr__(self) -> str:
        return f"<Rule {self.pattern!r}>"


class AppBlocker:
    def __init__(
        self,
        patterns: Iterable[str],
        mode: str = "polite",              # "polite" | "strict"
        grace_seconds: float = 2.0,
        scan_interval: float = 2.0,
        logger=None,
        dry_run: bool = False,
    ) -> None:
        self.rules: List[_Rule] = []
        for p in patterns or []:
            p = (p or "").strip()
            if not p:
                continue
            # normalize to match by filename (name/exe basename)
            self.rules.append(_Rule(pattern=p, lower=p.lower()))
        self.mode = mode.lower().strip() if mode else "polite"
        if self.mode not in ("polite", "strict"):
            self.mode = "polite"
        self.grace = max(0.0, float(grace_seconds))
        self.interval = max(0.5, float(scan_interval))
        self.logger = logger
        self.dry = bool(dry_run)
        self._stop = asyncio.Event()
        self._self_pid = os.getpid()

        # Some common critical/system names we never touch (defense in depth)
        self._never = {  # case-insensitive compare
            "system", "idle", "init", "launchd", "systemd", "wininit.exe", "services.exe",
            "csrss.exe", "lsass.exe", "smss.exe"
        }

    async def run(self) -> None:
        """Main periodic scan loop."""
        try:
            while not self._stop.is_set():
                await self._scan_once()
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
                except asyncio.TimeoutError:
                    pass
        except asyncio.CancelledError:
            return

    def stop(self) -> None:
        self._stop.set()

    async def _scan_once(self) -> None:
        # iterate with minimal info to reduce overhead
        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "username", "ppid"]):
            try:
                pid = proc.info.get("pid") or proc.pid
                if pid == self._self_pid:
                    continue
                name = (proc.info.get("name") or "") or ""
                exe = (proc.info.get("exe") or "") or ""
                base = os.path.basename(exe) if exe else name
                lname = (name or "").lower()
                lbase = (base or "").lower()

                # Never kill critical/system processes (belt & suspenders)
                if lname in self._never or lbase in self._never:
                    continue

                matched, rule = self._matches_any(lname, lbase)
                if not matched:
                    continue

                # Decide action
                if self.dry:
                    await self._log("APP", f"{base or name}", 0, "MATCH-DRYRUN", rule)
                    continue

                if self.mode == "polite":
                    await self._terminate(proc, base or name, rule, escalate=False)
                else:
                    await self._terminate(proc, base or name, rule, escalate=True)

            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            except psutil.AccessDenied:
                await self._log("APP", str(proc.pid), 0, "SKIP-ACCESSDENIED", "")
            except Exception as e:
                await self._log("APP", "scan", 0, f"ERROR {type(e).__name__}", str(e))

    def _matches_any(self, lname: str, lbase: str) -> Tuple[bool, str]:
        for r in self.rules:
            if r.match_name(lname) or r.match_name(lbase):
                return True, r.pattern
        return False, ""

    async def _terminate(self, proc: psutil.Process, display: str, rule: str, escalate: bool) -> None:
        pid = proc.pid
        try:
            proc.terminate()  # polite on all OS; Windows → TerminateProcess
            await self._log("APP", display, pid, "TERMINATE", f"rule={rule}")
            try:
                await asyncio.to_thread(proc.wait, timeout=self.grace if escalate else self.grace)
            except psutil.TimeoutExpired:
                if escalate:
                    try:
                        proc.kill()
                        await self._log("APP", display, pid, "KILL", f"rule={rule}")
                    except psutil.NoSuchProcess:
                        pass
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            await self._log("APP", display, pid, "SKIP-ACCESSDENIED", f"rule={rule}")
        except Exception as e:
            await self._log("APP", display, pid, f"ERROR {type(e).__name__}", f"rule={rule} {e}")

    async def _log(self, kind: str, host: str, port: int, decision: str, rule: str) -> None:
        if self.logger:
            try:
                await self.logger.write(kind, host, port, decision, rule)
                return
            except Exception:
                pass
        # fallback console log
        print(f"[{kind}] {host}:{port} {decision} {rule}")
