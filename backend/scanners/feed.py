"""
Social feed scrapers — extracts recent posts from each platform for engagement drafting.
Selectors are best-effort; they may need updating as platforms change their UI.
"""
from playwright.async_api import BrowserContext


async def scan_feed(ctx: BrowserContext, platform: str, max_posts: int = 10) -> list[dict]:
    scrapers = {
        "facebook": _scan_facebook,
        "instagram": _scan_instagram,
        "linkedin": _scan_linkedin,
        "twitter": _scan_twitter,
    }
    fn = scrapers.get(platform)
    if not fn:
        return []
    return await fn(ctx, max_posts)


async def _scan_facebook(ctx: BrowserContext, max_posts: int) -> list[dict]:
    page = await ctx.new_page()
    posts = []
    try:
        await page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"[feed/facebook] landed on: {page.url}")
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(900)

        # Use post links as anchors — more stable than pagelet selectors
        post_links = await page.query_selector_all(
            'a[href*="/posts/"], a[href*="story_fbid"], a[href*="?story_fbid"]'
        )
        print(f"[feed/facebook] found {len(post_links)} post links")
        seen_hrefs = set()
        for link_el in post_links[:max_posts * 3]:
            try:
                href = await link_el.get_attribute("href")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                # Walk up to find the feed story container
                article = await page.evaluate_handle(
                    "(el) => el.closest('[role=\"article\"]') || el.closest('[data-pagelet]')",
                    link_el
                )
                if not article:
                    continue

                # Author: h2 or h3 link text
                author_el = await article.query_selector("h2 a, h3 a, strong a")
                # Content: longest dir=auto text block
                candidates = await article.query_selector_all('[dir="auto"]')
                best = None
                best_len = 0
                for c in candidates:
                    t = (await c.inner_text()).strip()
                    if 10 < len(t) < 2000 and len(t) > best_len:
                        best_len = len(t)
                        best = c

                if not author_el:
                    print(f"[feed/facebook] skipping: no author_el")
                    continue
                if not best:
                    print(f"[feed/facebook] skipping: no content")
                    continue

                author = (await author_el.inner_text()).strip()
                content = (await best.inner_text()).strip()

                posts.append({
                    "target_name": author,
                    "post_content": content[:500],
                    "post_url": href,
                    "target_profile_url": None,
                })
                if len(posts) >= max_posts:
                    break
            except Exception as ex:
                print(f"[feed/facebook] item error: {ex}")
                continue
        print(f"[feed/facebook] extracted {len(posts)} posts")
    except Exception as e:
        print(f"[feed/facebook] error: {e}")
    finally:
        await page.close()
    return posts


async def _scan_instagram(ctx: BrowserContext, max_posts: int) -> list[dict]:
    page = await ctx.new_page()
    posts = []
    try:
        await page.goto("https://www.instagram.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)
        print(f"[feed/instagram] landed on: {page.url}")
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, 600)")
            await page.wait_for_timeout(1000)

        # Use post/reel links as anchors — stories won't have these
        post_links = await page.query_selector_all("a[href*='/p/'], a[href*='/reel/']")
        print(f"[feed/instagram] found {len(post_links)} post links")
        seen_hrefs = set()
        for link_el in post_links[:max_posts * 2]:
            try:
                href = await link_el.get_attribute("href")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                # Walk up to the article container
                article = await page.evaluate_handle(
                    "(el) => el.closest('article')", link_el
                )
                if not article:
                    continue

                # Author: first profile link inside the article (before the post link)
                author_links = await article.query_selector_all("a[href^='/'][href$='/']")
                author_el = author_links[0] if author_links else None

                # Caption: largest text block in the article
                spans = await article.query_selector_all("li span, div > span")
                best = None
                best_len = 0
                for s in spans:
                    t = (await s.inner_text()).strip()
                    if len(t) > best_len and len(t) < 2000:
                        best_len = len(t)
                        best = s

                if not author_el:
                    print(f"[feed/instagram] skipping: no author_el")
                    continue

                author = (await author_el.inner_text()).strip().rstrip("/")
                content = (await best.inner_text()).strip() if best else ""
                if not content or len(content) < 5:
                    print(f"[feed/instagram] skipping: no caption")
                    continue

                posts.append({
                    "target_name": author,
                    "post_content": content[:500],
                    "post_url": f"https://www.instagram.com{href}",
                    "target_profile_url": f"https://www.instagram.com/{author}/",
                })
                if len(posts) >= max_posts:
                    break
            except Exception as ex:
                print(f"[feed/instagram] item error: {ex}")
                continue
        print(f"[feed/instagram] extracted {len(posts)} posts")
    except Exception as e:
        print(f"[feed/instagram] error: {e}")
    finally:
        await page.close()
    return posts


async def _scan_linkedin(ctx: BrowserContext, max_posts: int) -> list[dict]:
    page = await ctx.new_page()
    posts = []
    try:
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"[feed/linkedin] landed on: {page.url}")
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(800)

        # Try multiple selector strategies for LinkedIn feed posts
        elements = await page.query_selector_all(
            ".feed-shared-update-v2, "
            ".occludable-update, "
            "[data-urn*='activity'], "
            ".scaffold-finite-scroll__content li"
        )
        print(f"[feed/linkedin] found {len(elements)} post elements")

        for el in elements[:max_posts]:
            try:
                author_el = await el.query_selector(
                    ".update-components-actor__name, "
                    ".feed-shared-actor__name, "
                    ".update-components-actor__title span[aria-hidden='true'], "
                    "a[data-field='actor'] span[aria-hidden='true']"
                )
                content_el = await el.query_selector(
                    ".feed-shared-text, "
                    ".update-components-text, "
                    ".feed-shared-update-v2__description, "
                    "[class*='commentary']"
                )
                link_el = await el.query_selector(
                    "a[href*='/posts/'], a[href*='/feed/update/']"
                )

                if not author_el:
                    print(f"[feed/linkedin] skipping: no author_el")
                    continue

                content = (await content_el.inner_text()).strip() if content_el else ""
                if not content:
                    continue

                posts.append({
                    "target_name": (await author_el.inner_text()).strip(),
                    "post_content": content[:500],
                    "post_url": await link_el.get_attribute("href") if link_el else None,
                    "target_profile_url": None,
                })
            except Exception as ex:
                print(f"[feed/linkedin] item error: {ex}")
                continue
        print(f"[feed/linkedin] extracted {len(posts)} posts")
    except Exception as e:
        print(f"[feed/linkedin] error: {e}")
    finally:
        await page.close()
    return posts


async def _scan_twitter(ctx: BrowserContext, max_posts: int) -> list[dict]:
    page = await ctx.new_page()
    posts = []
    try:
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"[feed/twitter] landed on: {page.url}")
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(800)

        tweets = await page.query_selector_all('[data-testid="tweet"]')
        print(f"[feed/twitter] found {len(tweets)} tweets")
        for el in tweets[:max_posts]:
            try:
                # Get the display name from User-Name container (first line of text)
                author_el = await el.query_selector('[data-testid="User-Name"]')
                content_el = await el.query_selector('[data-testid="tweetText"]')
                link_el = await el.query_selector('a[href*="/status/"]')

                if not author_el:
                    print(f"[feed/twitter] skipping: no author_el")
                    continue

                author_text = (await author_el.inner_text()).strip()
                # User-Name contains "Display Name\n@handle" — take just the display name
                author = author_text.split("\n")[0].strip()

                content = (await content_el.inner_text()).strip() if content_el else ""
                if not content:
                    print(f"[feed/twitter] skipping: no content (probably media-only)")
                    continue

                href = await link_el.get_attribute("href") if link_el else None
                posts.append({
                    "target_name": author,
                    "post_content": content[:280],
                    "post_url": f"https://x.com{href}" if href else None,
                    "target_profile_url": None,
                })
            except Exception as ex:
                print(f"[feed/twitter] item error: {ex}")
                continue
        print(f"[feed/twitter] extracted {len(posts)} posts")
    except Exception as e:
        print(f"[feed/twitter] error: {e}")
    finally:
        await page.close()
    return posts
