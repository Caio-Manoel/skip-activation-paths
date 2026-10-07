"""Capture README screenshots of the dashboard (requires `playwright` + Chromium)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob("*.png"):
    f.unlink()

with sync_playwright() as p:
    b = p.chromium.launch()
    errors = []
    for name, width in [("desktop", 1280), ("phone", 400)]:
        pg = b.new_page(viewport={"width": width, "height": 900}, device_scale_factor=1.5)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto((ROOT / "dashboard" / "index.html").as_uri())
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT / f"dashboard_{name}.png"), full_page=True)
        if name == "desktop":
            for sec in "ABCDEFG":
                pg.locator(f"#{sec}").screenshot(path=str(OUT / f"section_{sec}.png"))
        sw = pg.evaluate("document.documentElement.scrollWidth")
        print(name, "scrollWidth", sw)
    b.close()
print("errors:", errors or "none")
