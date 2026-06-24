import json
import os
from playwright.async_api import async_playwright, BrowserContext, Browser, Playwright

SESSION_DIR = os.getenv("SESSION_DIR", "sessions")
ROOT_PATH = chr(47)  # "/"


class PlaywrightManager:
    def __init__(self):
        self._playwright: Playwright = None
        self._browser: Browser = None
        self._contexts: dict[str, BrowserContext] = {}

    async def start(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )

    async def get_context(self, platform: str) -> BrowserContext:
        if platform in self._contexts:
            return self._contexts[platform]

        session_file = os.path.join(SESSION_DIR, f"{platform}.json")
        storage_state = session_file if os.path.exists(session_file) else None

        context = await self._browser.new_context(
            storage_state=storage_state,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        self._contexts[platform] = context
        return context

    async def save_session(self, platform: str):
        if platform in self._contexts:
            session_file = os.path.join(SESSION_DIR, f"{platform}.json")
            await self._contexts[platform].storage_state(path=session_file)

    async def import_cookies(self, platform: str, cookies: list[dict]):
        """Convert browser DevTools cookie export to Playwright storage state and save."""
        session_file = os.path.join(SESSION_DIR, f"{platform}.json")

        same_site_map = {
            "no_restriction": "None",
            "lax": "Lax",
            "strict": "Strict",
            "none": "None",
            "unspecified": "Lax",
            "": "Lax",
        }

        playwright_cookies = []
        for c in cookies:
            raw_same_site = (c.get("sameSite") or "").lower()
            same_site = same_site_map.get(raw_same_site, "Lax")
            playwright_cookies.append({
                "name": c.get("name", ""),
                "value": c.get("value", ""),
                "domain": c.get("domain", ""),
                "path": c.get("path", ROOT_PATH),
                "expires": float(c.get("expirationDate", -1)),
                "httpOnly": bool(c.get("httpOnly", False)),
                "secure": bool(c.get("secure", False)),
                "sameSite": same_site,
            })

        with open(session_file, "w") as f:
            json.dump({"cookies": playwright_cookies, "origins": []}, f)

        if platform in self._contexts:
            await self._contexts[platform].close()
            del self._contexts[platform]

    async def close(self):
        for context in self._contexts.values():
            await context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
