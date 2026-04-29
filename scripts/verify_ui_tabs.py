"""Headless UI verification harness.

Loads the live MeritScore UI at two viewports, switches through every Sword tab
for the default agent, and reports:
  - JS console errors / page errors per tab
  - Tab-bar overflow (scrollWidth > clientWidth) at each viewport
  - Screenshot per (viewport, tab) under docs/demo/screenshots/verify/

Run: python scripts/verify_ui_tabs.py [URL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://meritscore.warvis.org"
TABS = ["live", "tee", "wf", "ai", "zk", "uniswap", "mg"]
VIEWPORTS = [(1920, 1080), (1366, 768)]
OUT_DIR = Path("docs/demo/screenshots/verify")


def run() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict = {"url": URL, "viewports": []}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w, h in VIEWPORTS:
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            console_errs: list[str] = []
            page_errs: list[str] = []
            page.on("console", lambda m: console_errs.append(f"{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e: page_errs.append(str(e)))

            page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(".tab-btn", timeout=15000)
            page.wait_for_timeout(1500)

            overflow = page.evaluate(
                "() => { const el = document.querySelector('.tab-btn')?.parentElement; "
                "return el ? {client: el.clientWidth, scroll: el.scrollWidth, overflow: el.scrollWidth > el.clientWidth + 2} : null; }"
            )

            tab_results: list[dict] = []
            buttons = page.locator(".tab-btn")
            for idx, tab in enumerate(TABS):
                if buttons.count() > idx:
                    buttons.nth(idx).click()
                page.wait_for_timeout(800)
                shot = OUT_DIR / f"{w}x{h}_{tab}.png"
                page.screenshot(path=str(shot), full_page=False)
                tab_results.append({
                    "tab": tab,
                    "screenshot": str(shot),
                    "console_errors_so_far": list(console_errs),
                    "page_errors_so_far": list(page_errs),
                })

            report["viewports"].append({
                "size": f"{w}x{h}",
                "tab_bar": overflow,
                "tabs": tab_results,
                "final_console_errors": console_errs,
                "final_page_errors": page_errs,
            })
            ctx.close()
        browser.close()

    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, indent=2, default=str))
    # Concise summary
    print("\n=== SUMMARY ===")
    for vp in r["viewports"]:
        bar = vp["tab_bar"]
        print(f"[{vp['size']}] tab-bar overflow={bar['overflow'] if bar else '?'} "
              f"({bar['scroll']}/{bar['client']})  "
              f"console_errors={len(vp['final_console_errors'])} "
              f"page_errors={len(vp['final_page_errors'])}")
        for terr in vp["final_console_errors"]:
            print(f"  ! {terr}")
        for perr in vp["final_page_errors"]:
            print(f"  ! pageerror: {perr}")
