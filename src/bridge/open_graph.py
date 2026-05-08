"""Abre un HTML local en Chrome via CDP y screenshot."""
import sys, time, argparse
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--html", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--wait", type=int, default=10)
args = ap.parse_args()

file_url = "file:///" + args.html.replace("\\","/").replace(" ","%20")

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    print(f"[NAV] {file_url}")
    page.goto(file_url, wait_until="domcontentloaded", timeout=20000)
    time.sleep(args.wait)
    page.screenshot(path=args.out, full_page=False)
    print(f"[OK] {args.out}")
    print(f"[OK] Title: {page.title()}")
