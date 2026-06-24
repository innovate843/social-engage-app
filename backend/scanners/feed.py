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

        post_elements = await page.query_selector_all('[data-pagelet^="FeedUnit"]')
        if not post_elements:
            post_elements = await page.query_selector_all('[role="article"]')
        print(f"[feed/facebook] found {len(post_elements)} post elements")

        for el in post_elements[:max_posts]:
            try:
                # Author: try several selector patterns
                author_el = await el.query_selector(
                    "h2 a, h3 a, strong a, "
                    "[data-ad-comet-preview='actor'] a, "
                    "a[role='link'][tabindex='0'] span"
                )
                # Content: prefer message preview, fall back to any auto-direction block
                content_el = await el.query_selector('[data-ad-comet-preview="message"]')
                if not content_el:
                    # get all dir=auto spans and pick the longest
                    candidates = await el.query_selector_all('[dir="auto"]')
                    best = None
                    best_len = 0
                    for c in candidates:
                        t = (await c.inner_text()).strip()
                        if len(t) > best_len:
                            best_len = len(t)
                            best = c
                    content_el = best

                link_el = await el.query_selector('a[href*="/posts/"], a[href*="story_fbid"]')

                if not author_el:
                    print(f"[feed/facebook] skipping: no author_el")
                    continue
                if not content_el:
                    print(f"[feed/facebook] skipping: no content_el")
                    continue

                content = (await content_el.inner_text()).strip()
                author = (await author_el.inner_text()).strip()
                if len(content) < 10 or not author:
                    continue

                posts.append({
                    "target_name": author,
                    "post_content": content[:500],
                    "post_url": await link_el.get_attribute("href") if link_el else None,
                    "target_profile_url": None,
                })
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

        articles = await page.query_selector_all("article")
        print(f"[feed/instagram] found {len(articles)} articles")
        for el in articles[:max_posts]:
            try:
                # Author username
                author_el = await el.query_selector("header a[href]")
                # Caption — try the post caption span
                caption_el = await el.query_selector(
                    "div[class*='_a9zs'] span, "
                    "ul li span[class], "
                    "div > span > span"
                )
                if not caption_el:
                    spans = await el.query_selector_all("span")
                    best = None
                    best_len = 0
                    for s in spans:
                        t = (await s.inner_text()).strip()
                        if len(t) > best_len:
                            best_len = len(t)
                            best = s
                    caption_el = best

                link_el = await el.query_selector("a[href*='/p/'], a[href*='/reel/']")

                if not author_el:
                    print(f"[feed/instagram] skipping: no author_el")
                    continue

                author = (await author_el.inner_text()).strip()
                content = (await caption_el.inner_text()).strip() if caption_el else ""
                if not content or len(content) < 5:
                    continue

                href = await link_el.get_attribute("href") if link_el else None
                posts.append({
                    "target_name": author,
                    "post_content": content[:500],
                    "post_url": f"https://www.instagram.com{href}" if href else None,
                    "target_profile_url": f"https://www.instagram.com/{author}/",
                })
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
