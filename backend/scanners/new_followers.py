"""
Follow-back suggestions — finds people who recently followed you.
"""
from playwright.async_api import BrowserContext


async def scan_new_followers(ctx: BrowserContext, platform: str, max_results: int = 30) -> list[dict]:
    scrapers = {
        "twitter": _new_followers_twitter,
        "instagram": _new_followers_instagram,
    }
    fn = scrapers.get(platform)
    if not fn:
        return []
    return await fn(ctx, max_results)


async def _new_followers_twitter(ctx: BrowserContext, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        await page.goto("https://x.com/notifications", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"[followback/twitter] landed on: {page.url}")

        for _ in range(4):
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(800)

        cells = await page.query_selector_all('[data-testid="cellInnerDiv"]')
        print(f"[followback/twitter] found {len(cells)} notification cells")

        seen = set()
        for cell in cells:
            try:
                text = (await cell.inner_text()).strip().lower()
                if "followed you" not in text:
                    continue
                links = await cell.query_selector_all('a[href^="/"]')
                for link in links:
                    href = await link.get_attribute("href")
                    if not href or href in seen or "notifications" in href or href == "/":
                        continue
                    seen.add(href)
                    name = (await link.inner_text()).strip().split("\n")[0]
                    if name:
                        results.append({
                            "target_name": name,
                            "target_profile_url": f"https://x.com{href}",
                        })
                        break
                if len(results) >= max_results:
                    break
            except Exception:
                continue

        print(f"[followback/twitter] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[followback/twitter] error: {e}")
    finally:
        await page.close()
    return results


async def _new_followers_instagram(ctx: BrowserContext, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # Navigate to notifications (heart icon)
        notif_btn = await page.query_selector('a[href="/accounts/activity/"], svg[aria-label*="otif"], a[href*="activity"]')
        if notif_btn:
            await notif_btn.click()
            await page.wait_for_timeout(2500)
        else:
            await page.goto("https://www.instagram.com/accounts/activity/", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2500)

        print(f"[followback/instagram] landed on: {page.url}")

        for _ in range(2):
            await page.evaluate("window.scrollBy(0, 600)")
            await page.wait_for_timeout(800)

        items = await page.query_selector_all("div[class], li")
        seen = set()
        for item in items:
            try:
                text = (await item.inner_text()).strip().lower()
                if "started following" not in text and "followed you" not in text:
                    continue
                link_el = await item.query_selector("a[href^='/']")
                if not link_el:
                    continue
                href = await link_el.get_attribute("href")
                if not href or href in seen:
                    continue
                seen.add(href)
                name = (await link_el.inner_text()).strip()
                if name:
                    results.append({
                        "target_name": name,
                        "target_profile_url": f"https://www.instagram.com{href}",
                    })
                    if len(results) >= max_results:
                        break
            except Exception:
                continue

        print(f"[followback/instagram] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[followback/instagram] error: {e}")
    finally:
        await page.close()
    return results
