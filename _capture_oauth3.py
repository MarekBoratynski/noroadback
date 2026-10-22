"""Retake: 04, 05, 06 (with Continue click), 07. Reuses persistent profile.
Opens the branding URL first so user can verify/switch account before setting flag."""
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
FLAG = Path("/tmp/oauth_ready2")
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
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "scope": SCOPES,
    })
)
BRANDING_URL = f"https://console.cloud.google.com/auth/branding?project={PROJECT_ID}"
SCOPES_URL   = f"https://console.cloud.google.com/auth/scopes?project={PROJECT_ID}"
REVOKE_URL   = "https://myaccount.google.com/connections"

BANNER_JS = """
({url, today}) => {
  const bar = document.createElement('div');
  bar.style.cssText = `
    all: initial; display: block; position: fixed; top: 0; left: 0; right: 0;
    z-index: 2147483647; box-sizing: border-box; background: #1f6feb; color: #fff;
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; font-size: 13px;
    line-height: 1.4; padding: 10px 20px; border-bottom: 2px solid #0b4ab8;
  `;
  bar.textContent = `URL: ${url}   ·   Captured: ${today}`;
  document.body.appendChild(bar);
}
"""

def snap(page, name, url):
    try:
        page.evaluate(BANNER_JS, {"url": url, "today": TODAY})
    except Exception as e:
        print(f"   banner inject failed: {e!r}", flush=True)
    out = OUT / f"{name}.png"
    page.screenshot(path=str(out), full_page=True)
    print(f"   saved {out} ({out.stat().st_size} B)", flush=True)

# keep flag if present to allow quick re-runs

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE),
        headless=False,
        viewport={"width": 1440, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    # Pre-open the branding page so user can confirm/switch account
    try:
        page.goto(BRANDING_URL, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"preload: {e!r}", flush=True)

    print(f"[wait] Verify TOP-RIGHT avatar = marek88boratynski@gmail.com", flush=True)
    print(f"[wait] Then: touch {FLAG}", flush=True)
    waited = 0
    while not FLAG.exists():
        time.sleep(2); waited += 2
        if waited % 30 == 0: print(f"[wait] {waited}s", flush=True)
        if waited > 1800: raise SystemExit("timeout")
    print(f"[wait] flag seen after {waited}s", flush=True)

    # 04 — branding (retake)
    print("-> 04_oauth_branding", flush=True)
    try:
        page.goto(BRANDING_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        snap(page, "04_oauth_branding", BRANDING_URL)
    except Exception:
        traceback.print_exc()

    # 05 — scopes (retake)
    print("-> 05_oauth_scopes", flush=True)
    try:
        page.goto(SCOPES_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        snap(page, "05_oauth_scopes", SCOPES_URL)
    except Exception:
        traceback.print_exc()

    # 06 — consent full flow: open, click Gmail account, click Continue on unverified warning,
    # then capture the permissions-list screen (DO NOT click Allow).
    print("-> 06 full consent flow", flush=True)
    try:
        page.goto(CONSENT_URL, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        snap(page, "06a_consent_account_picker", page.url)

        # Click the user's Gmail account row
        try:
            page.get_by_text("marek88boratynski@gmail.com", exact=False).first.click(timeout=5000)
            print("   clicked gmail row", flush=True)
        except Exception as e:
            print(f"   gmail row click failed: {e!r}", flush=True)
        time.sleep(5)
        snap(page, "06b_after_account_pick", page.url)

        # If "Google hasn't verified this app" shows, click Continue (not Allow)
        clicked_continue = False
        for sel in ['button:has-text("Continue")', 'text=/^Continue$/i', 'a:has-text("Continue")']:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.click(timeout=5000)
                    clicked_continue = True
                    print(f"   clicked Continue via {sel}", flush=True)
                    break
            except Exception as e:
                print(f"   selector {sel}: {e!r}", flush=True)
        if not clicked_continue:
            print("   Continue not present (maybe already at scope list)", flush=True)
        time.sleep(5)
        snap(page, "06_oauth_consent_screen", page.url)
    except Exception:
        traceback.print_exc()

    # 07 — revocation
    print("-> 07_revocation", flush=True)
    try:
        page.goto(REVOKE_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(8)
        snap(page, "07_revocation", REVOKE_URL)
    except Exception:
        traceback.print_exc()

    print("[done] closing in 5s", flush=True)
    time.sleep(5)
    ctx.close()
