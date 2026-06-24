"""
Hashtag/keyword discovery — finds people posting with a hashtag to add to follow queue.
"""
from playwright.async_api import BrowserContext


async def scan_hashtag(ctx: BrowserContext, platform: str, hashtag: str, max_results: int = 20) -> list[dict]:
    scrapers = {
        "twitter": _hashtag_twitter,
        "instagram": _hashtag_instagram,
        "linkedin": _hashtag_linkedin,
    }
    fn = scrapers.get(platform)
    if not fn:
        return []
    tag = hashtag.lstrip("#")
    return await fn(ctx, tag, max_results)


async def _hashtag_twitter(ctx: BrowserContext, tag: str, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        await page.goto(
            f"https://x.com/search?q=%23{tag}&f=people",
            wait_until="domcontentloaded", timeout=30000
        )
        await page.wait_for_timeout(3000)
        print(f"[hashtag/twitter] landed on: {page.url}")

        seen = set()
        for _ in range(4):
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
            await page.wait_for_timeout(900)

        print(f"[hashtag/twitter] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[hashtag/twitter] error: {e}")
    finally:
        await page.close()
    return results[:max_results]


async def _hashtag_instagram(ctx: BrowserContext, tag: str, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        await page.goto(
            f"https://www.instagram.com/explore/tags/{tag}/",
            wait_until="domcontentloaded", timeout=30000
        )
        await page.wait_for_timeout(3000)
        print(f"[hashtag/instagram] landed on: {page.url}")

        post_links = await page.query_selector_all("a[href*='/p/'], a[href*='/reel/']")
        print(f"[hashtag/instagram] found {len(post_links)} posts to sample")

        seen = set()
        for link in post_links[:min(len(post_links), max_results * 2)]:
            if len(results) >= max_results:
                break
            try:
                href = await link.get_attribute("href")
                if not href:
                    continue
                post_page = await ctx.new_page()
                try:
                    await post_page.goto(
                        f"https://www.instagram.com{href}",
                        wait_until="domcontentloaded", timeout=20000
                    )
                    await post_page.wait_for_timeout(1500)
                    author_el = await post_page.query_selector("header a[href^='/']")
                    if author_el:
                        author_href = await author_el.get_attribute("href")
                        author = (await author_el.inner_text()).strip()
                        profile_url = f"https://www.instagram.com{author_href}"
                        if author and profile_url not in seen:
                            seen.add(profile_url)
                            results.append({
                                "target_name": author,
                                "target_profile_url": profile_url,
                            })
                finally:
                    await post_page.close()
            except Exception:
                continue

        print(f"[hashtag/instagram] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[hashtag/instagram] error: {e}")
    finally:
        await page.close()
    return results


async def _hashtag_linkedin(ctx: BrowserContext, tag: str, max_results: int) -> list[dict]:
    page = await ctx.new_page()
    results = []
    try:
        await page.goto(
            f"https://www.linkedin.com/search/results/content/?keywords=%23{tag}",
            wait_until="domcontentloaded", timeout=30000
        )
        await page.wait_for_timeout(3000)
        print(f"[hashtag/linkedin] landed on: {page.url}")

        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(800)

        profile_links = await page.query_selector_all("a[href*='/in/'], a[href*='/company/']")
        seen = set()
        for link in profile_links:
            try:
                href = await link.get_attribute("href")
                if not href:
                    continue
                clean = href.split("?")[0]
                if clean in seen or ("/in/" not in clean and "/company/" not in clean):
                    continue
                seen.add(clean)
                name_el = await link.query_selector("span[aria-hidden='true'], span")
                name = (await name_el.inner_text()).strip() if name_el else ""
                if not name:
                    continue
                full_url = clean if clean.startswith("http") else f"https://www.linkedin.com{clean}"
                results.append({"target_name": name, "target_profile_url": full_url})
                if len(results) >= max_results:
                    break
            except Exception:
                continue

        print(f"[hashtag/linkedin] extracted {len(results)} profiles")
    except Exception as e:
        print(f"[hashtag/linkedin] error: {e}")
    finally:
        await page.close()
    return results
