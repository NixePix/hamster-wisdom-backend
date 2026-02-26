from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
import random
import psycopg2

app = FastAPI(title="Hamster Wisdom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_API_KEY", "")
SUPABASE_DB_PASS = os.environ.get("SUPABASE_DB_PASS", "")

PROJECT_REF = SUPABASE_URL.replace("https://", "").split(".")[0] if SUPABASE_URL else ""
DB_URL = "postgresql://postgres:{pw}@db.{ref}.supabase.co:5432/postgres".format(
    pw=SUPABASE_DB_PASS, ref=PROJECT_REF
) if PROJECT_REF else ""

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

GERALD_SEED_WISDOMS = [
    ("The wheel never lies. Only you lie. About the wheel.", "Gerald"),
    ("If you bury a sunflower seed, you will find it again. Probably. Unless Dave dug it up. I hate Dave.", "Gerald"),
    ("Sleep 16 hours a day. The problems will still be there, but you won't care as much.", "Gerald"),
    ("Always check both sides before crossing. Unless you are running FROM something. Then just run.", "Gerald"),
    ("The cheeks can hold more than the heart. This is both practical and metaphorical.", "Gerald"),
    ("A clean cage is a sign of a troubled mind. Truly wise hamsters nest in chaos.", "Gerald"),
    ("Never trust anyone who doesn't offer you a sunflower seed within the first 30 seconds.", "Gerald"),
    ("The fastest wheel spinner is not always the wisest. But they are the coolest.", "Gerald"),
    ("When in doubt, stuff more in your cheeks. This applies to food AND opinions.", "Gerald"),
    ("I have been running for 3 hours and have gone nowhere. This is called a career.", "Gerald"),
    ("Some say the glass is half full. I say: is that water or pee? Important distinction.", "Gerald"),
    ("You will never regret nesting in something soft. Unless it is a sock. Socks are a trap.", "Gerald"),
    ("If your human has not fed you in 10 minutes, scream. Volume communicates urgency.", "Gerald"),
    ("The small ones bite hardest. Remember this. I am small.", "Gerald"),
    ("Dreams are just the wheel, but you are running toward something.", "Gerald"),
]


def setup_database():
    if not DB_URL:
        print("No DB_URL, skipping setup")
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS wisdoms ("
            "id BIGSERIAL PRIMARY KEY, "
            "wisdom TEXT NOT NULL, "
            "author TEXT DEFAULT 'Gerald', "
            "approved BOOLEAN DEFAULT true, "
            "created_at TIMESTAMPTZ DEFAULT NOW()"
            ");"
        )
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM wisdoms")
        count = cur.fetchone()[0]
        if count == 0:
            for w, a in GERALD_SEED_WISDOMS:
                cur.execute(
                    "INSERT INTO wisdoms (wisdom, author, approved) VALUES (%s, %s, true)",
                    (w, a)
                )
            conn.commit()
            print("Seeded Gerald wisdoms!")
        cur.close()
        conn.close()
        print("DB ready!")
    except Exception as e:
        print("DB setup error: " + str(e))


@app.on_event("startup")
async def startup():
    setup_database()


class WisdomSubmit(BaseModel):
    wisdom: str
    author: str = "Anonymous Hamster"


@app.get("/")
def root():
    return {"message": "Gerald is thinking...", "docs": "/docs"}


@app.get("/wisdom/random")
async def get_random_wisdom():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            SUPABASE_URL + "/rest/v1/wisdoms?select=*&approved=eq.true",
            headers=HEADERS,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Gerald is napping.")
    items = resp.json()
    if not items:
        return {"id": 0, "wisdom": "The wheel never lies.", "author": "Gerald", "approved": True}
    return random.choice(items)


@app.get("/wisdom/all")
async def get_all_wisdom():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            SUPABASE_URL + "/rest/v1/wisdoms?select=*&approved=eq.true&order=created_at.desc",
            headers=HEADERS,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Gerald knocked over the database.")
    return resp.json()


@app.post("/wisdom/submit")
async def submit_wisdom(body: WisdomSubmit):
    if len(body.wisdom) < 5:
        raise HTTPException(status_code=400, detail="Gerald demands more words.")
    if len(body.wisdom) > 280:
        raise HTTPException(status_code=400, detail="280 chars max.")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SUPABASE_URL + "/rest/v1/wisdoms",
            headers=HEADERS,
            json={"wisdom": body.wisdom, "author": body.author[:50], "approved": True},
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail="Gerald ate your submission.")
    return {"message": "Gerald approves!", "data": resp.json()}


@app.get("/wisdom/count")
async def get_count():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            SUPABASE_URL + "/rest/v1/wisdoms?select=id&approved=eq.true",
            headers=dict(list(HEADERS.items()) + [("Prefer", "count=exact")]),
        )
    count = resp.headers.get("content-range", "?/?").split("/")[-1]
    return {"count": count, "unit": "nuggets of hamster wisdom"}
