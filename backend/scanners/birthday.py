"""
Facebook birthday scanner.
Navigates to facebook.com/events/birthdays and extracts today's birthdays.
"""
from playwright.async_api import BrowserContext

BIRTHDAY_URL = "https://www.facebook.com/events/birthdays"


async def scan_birthdays(ctx: BrowserContext) -> list[dict]:
    """Return list of {target_name, target_profile_url} for today's FB birthdays."""
    page = await ctx.new_page()
    try:
        await page.goto(BIRTHDAY_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        items = []

        # FB renders birthday cards — selectors may need updates as FB changes its UI.
        # Try multiple selector patterns to be resilient.
        card_selectors = [
            '[data-testid="birthday-card"] a',
            ".birthday-card a",
            'div[role="article"] a[role="link"]',
        ]

        found_links = []
        for sel in card_selectors:
            found_links = await page.query_selector_all(sel)
            if found_links:
                break

        seen = set()
        for el in found_links:
            href = await el.get_attribute("href")
            text = (await el.inner_text()).strip()
            if not href or not text:
                continue
            # Skip event/group links, keep profile links
            if any(skip in href for skip in ["/events/", "/groups/", "/birthdays"]):
                continue
            profile_url = href.split("?")[0]
            if profile_url not in seen and text:
                seen.add(profile_url)
                items.append({
                    "target_name": text,
                    "target_profile_url": profile_url,
                })

        return items
    except Exception as e:
        print(f"[birthday scanner] error: {e}")
        return []
    finally:
        await page.close()
