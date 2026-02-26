from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
import random

app = FastAPI(title="Hamster Wisdom API 🐹")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

class WisdomSubmit(BaseModel):
    wisdom: str
    author: str = "Anonymous Hamster"

@app.get("/")
def root():
    return {"message": "🐹 Gerald the Hamster is spinning his wheel and thinking..."}

@app.get("/wisdom/random")
async def get_random_wisdom():
    """Get a random piece of Gerald's unhinged wisdom"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/wisdoms?select=*&approved=eq.true",
            headers=HEADERS,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Gerald is napping. Try again.")
    items = resp.json()
    if not items:
        return {
            "id": 0,
            "wisdom": "The wheel never lies. Only you lie. About the wheel.",
            "author": "Gerald",
            "approved": True,
        }
    return random.choice(items)

@app.get("/wisdom/all")
async def get_all_wisdom():
    """Get all approved wisdom"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/wisdoms?select=*&approved=eq.true&order=created_at.desc",
            headers=HEADERS,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Gerald knocked over the database.")
    return resp.json()

@app.post("/wisdom/submit")
async def submit_wisdom(body: WisdomSubmit):
    """Submit your own hamster wisdom (goes into the pending pile)"""
    if len(body.wisdom) < 5:
        raise HTTPException(status_code=400, detail="Gerald demands more words.")
    if len(body.wisdom) > 280:
        raise HTTPException(status_code=400, detail="Even Gerald has limits. 280 chars max.")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/wisdoms",
            headers=HEADERS,
            json={
                "wisdom": body.wisdom,
                "author": body.author[:50],
                "approved": True,  # auto-approve for fun
            },
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail="Gerald ate your submission. Try again.")
    return {"message": "✅ Gerald approves. Your wisdom joins the wheel.", "data": resp.json()}

@app.get("/wisdom/count")
async def get_count():
    """How many wisdoms does Gerald hold?"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/wisdoms?select=count&approved=eq.true",
            headers={**HEADERS, "Prefer": "count=exact"},
        )
    count = resp.headers.get("content-range", "?/?").split("/")[-1]
    return {"count": count, "unit": "nuggets of hamster wisdom"}
