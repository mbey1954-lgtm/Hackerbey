import os, json, csv, uuid, threading, re
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import uvicorn

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")

DATA_DIR = "data"
RAW_DIR = f"{DATA_DIR}/raw"
INDEX_FILE = f"{DATA_DIR}/index.json"

os.makedirs(RAW_DIR, exist_ok=True)

app = FastAPI()
INDEX = []

# ─────────────────────────────
# YARDIMCI
# ─────────────────────────────
def norm(v):
    return re.sub(r"\s+", " ", str(v).upper().strip())

# ─────────────────────────────
# INDEX YÜKLE / KAYDET
# ─────────────────────────────
def load_index():
    global INDEX
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, encoding="utf-8") as f:
            INDEX = json.load(f)

def save_index():
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(INDEX, f, ensure_ascii=False)

load_index()

# ─────────────────────────────
# DOSYA PARSE
# ─────────────────────────────
def parse_file(path):
    records = []

    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            records = json.load(f)

    elif path.endswith(".csv"):
        with open(path, encoding="utf-8") as f:
            records = list(csv.DictReader(f))

    else:  # txt
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                p = line.strip().split("|")
                if len(p) >= 2:
                    records.append({"tc": p[0], "gsm": p[1]})

    for r in records:
        clean = {k.lower(): norm(v) for k, v in r.items()}
        INDEX.append(clean)

    save_index()
    return len(records)

# ─────────────────────────────
# TELEGRAM BOT
# ─────────────────────────────
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()

    path = f"{RAW_DIR}/{uuid.uuid4()}_{doc.file_name}"
    await file.download_to_drive(path)

    count = parse_file(path)

    await update.message.reply_text(
        f"✅ Yüklendi\n"
        f"📦 Kayıt: {count}\n\n"
        f"🌐 API:\n"
        f"{BASE_URL}/query?q=DEGER\n"
        f"{BASE_URL}/query?tc=TC&gsm=GSM"
    )

# ─────────────────────────────
# AKILLI + ALAN BAZLI API
# ─────────────────────────────
@app.get("/query")
def query(
    q: str = Query(None),
    tc: str = Query(None),
    gsm: str = Query(None),
    ad: str = Query(None),
    soyad: str = Query(None),
    il: str = Query(None),
    ilce: str = Query(None),
    anne: str = Query(None),
    baba: str = Query(None),
):
    results = []

    for r in INDEX:
        ok = True

        for key, val in {
            "tc": tc, "gsm": gsm, "ad": ad, "soyad": soyad,
            "il": il, "ilce": ilce, "anne": anne, "baba": baba
        }.items():
            if val and norm(val) not in r.get(key, ""):
                ok = False
                break

        if q and q.upper() not in json.dumps(r):
            ok = False

        if ok:
            results.append(r)

    if not results:
        return {"status": "not_found"}

    if len(results) == 1:
        return results[0]

    txt = f"results_{uuid.uuid4()}.txt"
    with open(txt, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return FileResponse(txt, filename="results.txt")

# ─────────────────────────────
# BOT THREAD
# ─────────────────────────────
def run_bot():
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    bot.run_polling()

threading.Thread(target=run_bot).start()

# ─────────────────────────────
# FASTAPI
# ─────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
