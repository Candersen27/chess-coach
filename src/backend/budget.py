"""
Demo-budget guard for the public deployment.

Tracks Anthropic token usage so a public visitor can try Claude coaching on
the server's key without running up the bill:

  - PER-IP daily cap  -> what each visitor's "budget left" bar reads from
  - GLOBAL daily cap  -> hard backstop protecting total spend

State is in-memory and resets on date change (and on container restart/wake).
That's an accepted tradeoff for a portfolio demo; a DB/Redis store is the
future upgrade. BYOK requests skip this guard entirely.
"""

import os
from datetime import date


def tokens_charged(usage: dict) -> int:
    """Tokens to bill against the demo budget for one Claude call.

    Counts fresh input + output + cache CREATION (the ~57K one-time book
    write, billed at 1.25x — the real cost driver). Skips cache READS, which
    are reported separately and billed at only ~0.1x, so charging them would
    drain a visitor's bar for nearly-free tokens.
    """
    if not usage:
        return 0
    return (
        usage.get("input_tokens", 0)
        + usage.get("output_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
    )


class BudgetGuard:
    def __init__(self):
        # Defaults sized so the ~57K one-time book cache-write doesn't exhaust
        # a visitor in a single message. Tune via fly secrets after watching
        # real spend.
        self.per_ip_cap = int(os.getenv("PER_IP_TOKEN_CAP", "150000"))
        self.global_cap = int(os.getenv("DAILY_TOKEN_CAP", "1000000"))
        self._day = date.today()
        self._per_ip: dict[str, int] = {}
        self._global = 0

    def _rollover(self):
        """Reset all counters when the calendar day changes."""
        today = date.today()
        if today != self._day:
            self._day = today
            self._per_ip.clear()
            self._global = 0

    def check(self, ip: str) -> bool:
        """True if this IP has room AND the global ceiling isn't reached."""
        self._rollover()
        return self._per_ip.get(ip, 0) < self.per_ip_cap and self._global < self.global_cap

    def record(self, ip: str, tokens: int):
        """Add token usage to both the per-IP and global counters."""
        self._rollover()
        self._per_ip[ip] = self._per_ip.get(ip, 0) + max(0, tokens)
        self._global += max(0, tokens)

    def status(self, ip: str) -> dict:
        """Per-IP budget snapshot for the frontend meter."""
        self._rollover()
        used = self._per_ip.get(ip, 0)
        remaining = max(0, self.per_ip_cap - used)
        remaining_pct = round(100 * remaining / self.per_ip_cap) if self.per_ip_cap else 0
        return {"used": used, "cap": self.per_ip_cap, "remaining_pct": remaining_pct}


# Shared instance for the app.
guard = BudgetGuard()


def client_ip(request) -> str:
    """Resolve the real visitor IP.

    Behind Fly's proxy, request.client.host is the proxy, so prefer the
    forwarded headers. Falls back to the socket peer for local dev.
    """
    fly_ip = request.headers.get("Fly-Client-IP")
    if fly_ip:
        return fly_ip
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
