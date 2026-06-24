import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import Database
from playwright_mgr import PlaywrightManager
from ai_drafter import draft_birthday_message, draft_reply
from scanners.birthday import scan_birthdays
from scanners.feed import scan_feed
from actions.post import post_birthday, post_reply, do_follow

db = Database()
pw = PlaywrightManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    await pw.start()
    yield
    await pw.close()


app = FastAPI(title="Social Engage API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ── Models ────────────────────────────────────────────────────────────────────

class UpdateDraftRequest(BaseModel):
    draft_message: str

class CookieImportRequest(BaseModel):
    cookies: list[dict]

class FollowRequest(BaseModel):
    platform: str
    name: str
    profile_url: str

class BirthdayAddRequest(BaseModel):
    name: str
    platform: str = "facebook"
    profile_url: str
    birthday_month: int
    birthday_day: int

class ScanFeedRequest(BaseModel):
    platforms: Optional[list[str]] = None


# ── Queue ─────────────────────────────────────────────────────────────────────

@app.get("/queue")
async def get_queue(status: str = "pending", type: str = None):
    return await db.get_queue(status=status, type=type)

@app.get("/queue/{item_id}")
async def get_queue_item(item_id: int):
    item = await db.get_queue_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.patch("/queue/{item_id}")
async def update_draft(item_id: int, body: UpdateDraftRequest):
    await db.update_draft(item_id, body.draft_message)
    return {"ok": True}

@app.post("/queue/{item_id}/approve")
async def approve_item(item_id: int):
    await db.set_status(item_id, "approved")
    return {"ok": True}

@app.post("/queue/{item_id}/reject")
async def reject_item(item_id: int):
    await db.set_status(item_id, "rejected")
    return {"ok": True}

@app.post("/queue/{item_id}/post")
async def post_item(item_id: int):
    item = await db.get_queue_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item["status"] not in ("approved", "pending"):
        raise HTTPException(status_code=400, detail="Item must be pending or approved to post")

    ctx = await pw.get_context(item["platform"])

    if item["type"] == "birthday":
        await post_birthday(ctx, item)
    elif item["type"] == "reply":
        await post_reply(ctx, item)
    elif item["type"] == "follow":
        await do_follow(ctx, item)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown type: {item['type']}")

    await db.set_status(item_id, "posted")
    await pw.save_session(item["platform"])
    return {"ok": True}


# ── Platforms ─────────────────────────────────────────────────────────────────

@app.get("/platforms")
async def get_platforms():
    return await db.get_platforms()

@app.post("/platforms/{platform}/cookies")
async def import_cookies(platform: str, body: CookieImportRequest):
    supported = {"facebook", "instagram", "linkedin", "twitter"}
    if platform not in supported:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    await pw.import_cookies(platform, body.cookies)
    await db.set_platform_logged_in(platform, True)
    return {"ok": True}

@app.delete("/platforms/{platform}/session")
async def clear_session(platform: str):
    import os
    session_file = f"sessions/{platform}.json"
    if os.path.exists(session_file):
        os.remove(session_file)
    await db.set_platform_logged_in(platform, False)
    return {"ok": True}


# ── Scans ─────────────────────────────────────────────────────────────────────

@app.post("/scan/birthdays")
async def trigger_birthday_scan():
    today = datetime.date.today()
    added = 0

    # Check manually-added birthdays for today
    for b in await db.get_todays_birthdays():
        draft = await draft_birthday_message(b["name"], b["platform"])
        await db.add_queue_item({
            "type": "birthday",
            "platform": b["platform"],
            "target_name": b["name"],
            "target_profile_url": b["profile_url"],
            "draft_message": draft,
        })
        await db.mark_birthday_wished(b["id"], today.year)
        added += 1

    # Scrape Facebook birthdays page
    ctx = await pw.get_context("facebook")
    for item in await scan_birthdays(ctx):
        draft = await draft_birthday_message(item["target_name"], "facebook")
        await db.add_queue_item({**item, "type": "birthday", "platform": "facebook", "draft_message": draft})
        added += 1

    return {"added": added}

@app.post("/scan/feed")
async def trigger_feed_scan(body: ScanFeedRequest = None):
    platforms = (body.platforms if body and body.platforms else None) or [
        "facebook", "instagram", "linkedin", "twitter"
    ]
    total = 0
    for platform in platforms:
        ctx = await pw.get_context(platform)
        for post in await scan_feed(ctx, platform):
            draft = await draft_reply(post["post_content"], platform, post["target_name"])
            await db.add_queue_item({**post, "type": "reply", "platform": platform, "draft_message": draft})
            total += 1
    return {"added": total}


# ── Manual adds ───────────────────────────────────────────────────────────────

@app.post("/follow")
async def add_follow(body: FollowRequest):
    await db.add_queue_item({
        "type": "follow",
        "platform": body.platform,
        "target_name": body.name,
        "target_profile_url": body.profile_url,
        "draft_message": f"Follow {body.name}",
    })
    return {"ok": True}

@app.post("/birthday")
async def add_birthday(body: BirthdayAddRequest):
    await db.add_birthday(body.model_dump())
    return {"ok": True}

@app.get("/health")
async def health():
    return {"ok": True}
