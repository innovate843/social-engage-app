"""
Competitor audience targeting — scrapes followers/following of any public profile.
"""
from playwright.async_api import BrowserContext


async def scan_audience(
    ctx: BrowserContext, platform: str, profile_url: str,
    source: str = "followers", max_results: int = 30
) -> list[dict]:
    scrapers = {
        "twitter": _audience_twitter,
        "instagram": _audience_instagram,
    }
    fn = scrapers.get(platform)
    if not fn:
        return []
    return await fn(ctx, profile_url, source, max_results)


async def _audience_twitter(ctx: BrowserContext, profile_url: str, source: str, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        username = profile_url.rstrip("/").split("/")[-1].lstrip("@")
        url = f"https://x.com/{username}/{source}"

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"[audience/twitter] landed on: {page.url}")

        seen = set()
        for _ in range(6):
            cells = await page.query_selector_all('[data-testid="UserCell"]')
            for cell in cells:
                try:
                    name_el = await cell.query_selector('[data-testid="User-Name"]')
                    link_el = await cell.query_selector('a[href^="/"]')
                    if not name_el or not link_el:
                        continue
                    href = await link_el.get_attribute("href")
                    if not href or href in seen or href == "/":
                        continue
                    seen.add(href)
                    name = (await name_el.inner_text()).strip().split("\n")[0]
                    results.append({
                        "target_name": name,
                        "target_profile_url": f"https://x.com{href}",
                    })
                except Exception:
                    continue
            if len(results) >= max_results:
                break
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(1000)

        print(f"[audience/twitter] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[audience/twitter] error: {e}")
    finally:
        await page.close()
    return results[:max_results]


async def _audience_instagram(ctx: BrowserContext, profile_url: str, source: str, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)
        print(f"[audience/instagram] landed on: {page.url}")

        link_text = "followers" if source == "followers" else "following"
        btn = None
        for a in await page.query_selector_all("a[href]"):
            href = await a.get_attribute("href")
            if href and link_text in href:
                btn = a
                break

        if not btn:
            raise Exception(f"Could not find {link_text} link")

        await btn.click()
        await page.wait_for_timeout(2500)

        seen = set()
        for _ in range(6):
            links = await page.query_selector_all("div[role='dialog'] a[href^='/']")
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    if not href or href in seen or href == "/":
                        continue
                    seen.add(href)
                    text = (await link.inner_text()).strip()
                    if text and len(text) < 50:
                        results.append({
                            "target_name": text,
                            "target_profile_url": f"https://www.instagram.com{href}",
                        })
                except Exception:
                    continue
            if len(results) >= max_results:
                break
            modal = await page.query_selector("div[role='dialog'] div[style*='overflow'], div[role='dialog'] ul")
            if modal:
                await modal.evaluate("el => el.scrollBy(0, 500)")
            await page.wait_for_timeout(1000)

        print(f"[audience/instagram] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[audience/instagram] error: {e}")
    finally:
        await page.close()
    return results[:max_results]
