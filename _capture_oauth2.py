"""Resume capture: reuses persistent profile (already logged in). Robust per-target error handling."""
from __future__ import annotations
import datetime as dt
import sys
import time
import traceback
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(line_buffering=True)

HOME = Path.home()
PROFILE = HOME / ".yt-audit-profile"
OUT = HOME / "Downloads" / "youtube-api-audit"
OUT.mkdir(parents=True, exist_ok=True)
TODAY = dt.date.today().isoformat()

PROJECT_ID = "youtugbenoroadback"
CLIENT_ID = "386437866823-ou3jb3mh7dqo2i8gjkbu8j6d2mup50e6.apps.googleusercontent.com"
REDIRECT = "http://localhost:8080/"
SCOPES = " ".join([
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
])

CONSENT_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    + urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "scope": SCOPES,
    })
)

TARGETS = [
    ("04_oauth_branding",       f"https://console.cloud.google.com/auth/branding?project={PROJECT_ID}"),
    ("05_oauth_scopes",         f"https://console.cloud.google.com/auth/scopes?project={PROJECT_ID}"),
    ("06_oauth_consent_screen", CONSENT_URL),
    ("07_revocation",           "https://myaccount.google.com/connections"),
]

BANNER_JS = """
(url, today) => {
  const bar = document.createElement('div');
  bar.style.cssText = `
    all: initial;
    display: block;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 2147483647;
    box-sizing: border-box;
    background: #1f6feb;
    color: #ffffff;
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 13px;
    line-height: 1.4;
    padding: 10px 20px;
    border-bottom: 2px solid #0b4ab8;
  `;
  bar.textContent = `URL: ${url}   ·   Captured: ${today}`;
  document.body.appendChild(bar);
}
"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE),
        headless=False,
        viewport={"width": 1440, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    for name, url in TARGETS:
        print(f"-> {name}: {url}", flush=True)
        try:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"   domcontentloaded failed: {e!r}", flush=True)
            # let interactive UI settle
            time.sleep(6)
            try:
                page.evaluate(BANNER_JS, [url, TODAY])
            except Exception as e:
                print(f"   banner inject failed: {e!r}", flush=True)
            out = OUT / f"{name}.png"
            page.screenshot(path=str(out), full_page=True)
            print(f"   saved {out} ({out.stat().st_size} B)", flush=True)
        except Exception:
            print(f"   FAILED {name}:", flush=True)
            traceback.print_exc()
            # take an emergency viewport screenshot
            try:
                emer = OUT / f"{name}_FALLBACK.png"
                page.screenshot(path=str(emer), full_page=False)
                print(f"   fallback saved {emer}", flush=True)
            except Exception as e2:
                print(f"   fallback also failed: {e2!r}", flush=True)

    print("[done] leaving browser open 10s then closing", flush=True)
    time.sleep(10)
    ctx.close()
