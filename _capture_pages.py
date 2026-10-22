"""One-shot: full-page screenshots + PDFs of the public site.
Adds a top banner with the full URL + date, since headless has no address bar.
"""
from __future__ import annotations
import datetime as dt
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path.home() / "Downloads" / "youtube-api-audit"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://marekboratynski.github.io/noroadback"
TODAY = dt.date.today().isoformat()

TARGETS = [
    ("01_privacy_policy", f"{BASE}/privacy.html", True),
    ("02_homepage",       f"{BASE}/",             False),
    ("03_terms_of_service", f"{BASE}/terms.html", True),
]

BANNER_JS = """
(url, today) => {
  const bar = document.createElement('div');
  bar.style.cssText = `
    all: initial;
    display: block;
    position: static;
    width: 100%;
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
  document.body.insertBefore(bar, document.body.firstChild);
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    for name, url, make_pdf in TARGETS:
        print(f"-> {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.evaluate(BANNER_JS, [url, TODAY])
        png = OUT / f"{name}.png"
        page.screenshot(path=str(png), full_page=True)
        print(f"   PNG {png} ({png.stat().st_size} B)")
        if make_pdf:
            pdf = OUT / f"{name}.pdf"
            page.emulate_media(media="screen")
            page.pdf(path=str(pdf), format="A4", print_background=True,
                     margin={"top":"10mm","right":"10mm","bottom":"10mm","left":"10mm"})
            print(f"   PDF {pdf} ({pdf.stat().st_size} B)")
    ctx.close()
    browser.close()
print("done")
