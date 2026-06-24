import os
import anthropic

_client = None

PLATFORM_HINTS = {
    "facebook": "Facebook (casual, personal, a few warm sentences)",
    "instagram": "Instagram (brief, upbeat, 1-2 relevant emojis OK)",
    "linkedin": "LinkedIn (professional but warm, no emojis)",
    "twitter": "X/Twitter (conversational, under 240 characters)",
}


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


async def draft_birthday_message(name: str, platform: str) -> str:
    hint = PLATFORM_HINTS.get(platform, platform)
    response = get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                f"Write a warm, genuine birthday message for {name} to post on {hint}. "
                f"Write in first person, from me. Natural and friendly — not corporate or sappy. "
                f"Just the message text, nothing else."
            ),
        }],
    )
    return response.content[0].text.strip()


async def draft_reply(post_content: str, platform: str, author: str) -> str:
    hint = PLATFORM_HINTS.get(platform, platform)
    response = get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=250,
        messages=[{
            "role": "user",
            "content": (
                f"Draft a genuine, engaging reply to this {hint} post by {author}:\n\n"
                f'"{post_content}"\n\n'
                f"Write as me. Add value, show real interest, or ask a thoughtful question. "
                f"Keep it natural — not formal or overly enthusiastic. "
                f"Just the reply text, nothing else."
            ),
        }],
    )
    return response.content[0].text.strip()
