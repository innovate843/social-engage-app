"""
Playwright posting actions — birthday posts, comment replies, follow.
Selectors are best-effort and may need tuning as platforms update their UI.
"""
from playwright.async_api import BrowserContext


async def post_birthday(ctx: BrowserContext, item: dict):
    """Post a birthday wall message on Facebook."""
    page = await ctx.new_page()
    try:
        await page.goto(item["target_profile_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # Try multiple selectors for the timeline composer
        composer_selectors = [
            '[aria-label*="Write on"]',
            '[aria-label*="timeline"]',
            '[data-testid="timeline-composer-text"]',
            'div[role="textbox"][aria-label*="Write"]',
        ]
        composer = None
        for sel in composer_selectors:
            composer = await page.query_selector(sel)
            if composer:
                break

        if not composer:
            raise Exception("Could not find Facebook timeline composer — selectors may need updating")

        await composer.click()
        await page.wait_for_timeout(800)
        await page.keyboard.type(item["draft_message"], delay=25)
        await page.wait_for_timeout(500)

        post_btn = await page.query_selector('[aria-label="Post"], button[type="submit"]')
        if post_btn:
            await post_btn.click()
            await page.wait_for_timeout(2000)
        else:
            raise Exception("Could not find Post button")
    finally:
        await page.close()


async def post_reply(ctx: BrowserContext, item: dict):
    """Post a comment/reply on any platform."""
    platform = item["platform"]
    post_url = item.get("post_url")
    if not post_url:
        raise Exception("No post URL provided for reply")

    page = await ctx.new_page()
    try:
        await page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        selectors = {
            "facebook": '[aria-label*="comment"], [data-testid="UFI2CommentInputField"]',
            "instagram": 'textarea[aria-label*="comment"], textarea[placeholder*="comment"]',
            "linkedin": '.comments-comment-texteditor, [placeholder*="Add a comment"]',
            "twitter": '[data-testid="tweetTextarea_0"]',
        }

        sel = selectors.get(platform, 'textarea, [role="textbox"]')
        box = await page.query_selector(sel)

        # Some platforms hide the box until you click a "Comment" button
        if not box:
            trigger = await page.query_selector(
                '[aria-label*="Comment"], button:has-text("Comment"), '
                '[aria-label*="Reply"], button:has-text("Reply")'
            )
            if trigger:
                await trigger.click()
                await page.wait_for_timeout(1000)
                box = await page.query_selector(sel)

        if not box:
            raise Exception(f"Could not find comment box on {platform}")

        await box.click()
        await page.keyboard.type(item["draft_message"], delay=25)
        await page.wait_for_timeout(500)

        # Twitter needs Ctrl+Enter; others accept Enter
        if platform == "twitter":
            await page.keyboard.press("Control+Enter")
        else:
            await page.keyboard.press("Enter")

        await page.wait_for_timeout(2000)
    finally:
        await page.close()


async def do_unfollow(ctx: BrowserContext, item: dict):
    """Click Unfollow on a profile."""
    platform = item["platform"]
    profile_url = item.get("target_profile_url")
    if not profile_url:
        raise Exception("No profile URL provided for unfollow")

    page = await ctx.new_page()
    try:
        await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        selectors = {
            "facebook": '[aria-label="Following"], button:has-text("Following")',
            "instagram": 'button:has-text("Following")',
            "linkedin": 'button:has-text("Following")',
            "twitter": '[data-testid*="unfollow"], button:has-text("Following")',
        }
        sel = selectors.get(platform, 'button:has-text("Following")')
        btn = await page.query_selector(sel)
        if not btn:
            raise Exception(f"Could not find Following button on {platform}")

        await btn.click()
        await page.wait_for_timeout(1500)

        confirm = await page.query_selector(
            'button:has-text("Unfollow"), [data-testid="confirmationSheetConfirm"]'
        )
        if confirm:
            await confirm.click()
            await page.wait_for_timeout(1500)
    finally:
        await page.close()


async def do_follow(ctx: BrowserContext, item: dict):
    """Click the Follow button on a profile."""
    platform = item["platform"]
    profile_url = item.get("target_profile_url")
    if not profile_url:
        raise Exception("No profile URL provided for follow")

    page = await ctx.new_page()
    try:
        await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        selectors = {
            "facebook": '[aria-label="Follow"], button:has-text("Follow")',
            "instagram": 'button:has-text("Follow")',
            "linkedin": 'button:has-text("Follow"), button:has-text("Connect")',
            "twitter": '[data-testid*="follow"], button:has-text("Follow")',
        }

        sel = selectors.get(platform, 'button:has-text("Follow")')
        btn = await page.query_selector(sel)
        if not btn:
            raise Exception(f"Could not find Follow button on {platform}")

        await btn.click()
        await page.wait_for_timeout(2000)
    finally:
        await page.close()
