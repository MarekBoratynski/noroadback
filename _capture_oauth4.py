"""Only steps 05, 06 (click Gmail + Continue), 07. Short, resilient."""
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
TODAY = dt.date.today().isoformat()
PROJECT_ID = "noroadback"
CLIENT_ID = "1047755517465-og12s2bnncn94qei8ucp9vm7nkg5trb4.apps.googleusercontent.com"
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
        "client_id": CLIENT_ID, "redirect_uri": REDIRECT,
        "response_type": "code", "access_type": "offline",
        "prompt": "consent", "include_granted_scopes": "true",
        "scope": SCOPES,
    })
)
SCOPES_URL = f"https://console.cloud.google.com/auth/scopes?project={PROJECT_ID}"
REVOKE_URL = "https://myaccount.google.com/connections"

BANNER_JS = """
({url, today}) => {
  const bar = document.createElement('div');
  bar.style.cssText = `all: initial; display:block; position:fixed; top:0; left:0; right:0;
    z-index:2147483647; box-sizing:border-box; background:#1f6feb; color:#fff;
    font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif; font-size:13px;
    line-height:1.4; padding:10px 20px; border-bottom:2px solid #0b4ab8;`;
  bar.textContent = `URL: ${url}   ·   Captured: ${today}`;
  document.body.appendChild(bar);
}
"""
def snap(page, name, url):
    try: page.evaluate(BANNER_JS, {"url": url, "today": TODAY})
    except Exception as e: print(f"banner: {e!r}", flush=True)
    out = OUT / f"{name}.png"
    page.screenshot(path=str(out), full_page=True)
    print(f"saved {out} ({out.stat().st_size} B)", flush=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE), headless=False, viewport={"width":1440,"height":900},
        args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    # 05 — scopes (take with scroll to show full page)
    print("-> 05", flush=True)
    try:
        page.goto(SCOPES_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(8)
        snap(page, "05_oauth_scopes", SCOPES_URL)
    except Exception: traceback.print_exc()

    # 06 — consent flow
    print("-> 06", flush=True)
    try:
        page.goto(CONSENT_URL, wait_until="domcontentloaded", timeout=45000)
        time.sleep(6)
        snap(page, "06a_consent_account_picker", page.url)
        try:
            page.get_by_text("marek88boratynski@gmail.com", exact=False).first.click(timeout=5000)
            print("clicked gmail", flush=True)
        except Exception as e:
            print(f"gmail click fail: {e!r}", flush=True)
        time.sleep(6)
        snap(page, "06b_after_pick", page.url)
        # Try Continue (unverified warning)
        for sel in ['button:has-text("Continue")','text=/^Continue$/i','a:has-text("Continue")']:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.click(timeout=5000)
                    print(f"clicked Continue via {sel}", flush=True); break
            except Exception as e: print(f"{sel}: {e!r}", flush=True)
        time.sleep(6)
        snap(page, "06_oauth_consent_screen", page.url)
    except Exception: traceback.print_exc()

    # 07 — revocation
    print("-> 07", flush=True)
    try:
        page.goto(REVOKE_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(10)
        snap(page, "07_revocation", REVOKE_URL)
    except Exception: traceback.print_exc()

    print("[done]", flush=True)
    time.sleep(3)
    ctx.close()
