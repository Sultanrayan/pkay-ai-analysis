"""Public JSON API (v3) served over aiohttp alongside the Telegram webhook.

Two endpoints are exposed:

* ``POST /api/v3/analyze`` — runs the multi-agent analysis for a Data Pair.
* ``POST /api/v3/agents``  — returns the callable AI Agent Team functions only
  (no analysis, no user-supplied model).

The HTTP layer is mounted in the same process as the Telegram webhook so a
single port serves both.
"""

from .server import create_web_app

__all__ = ["create_web_app"]
