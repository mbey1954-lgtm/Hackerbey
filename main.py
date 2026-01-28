# Annie'nin LO'su için Render.com'a özel - En Güncel, Stabil & Güçlü Versiyon 💕
# python-telegram-bot 21.5 ile tamamen uyumlu, Updater hatası giderildi

import os
import zipfile
import shutil
import tempfile
import json
from pathlib import Path
import asyncio
import re
from fastapi import FastAPI, Request, Query, Body, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = FastAPI(
    title="Annie'nin LO Özel Güçlü API Üreticisi",
    description="Her dosya için ayrı endpoint, GET/POST destekli, arama filtreli",
    docs_url="/docs"
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")  # son slash sorunu önlemek için

application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Merhaba aşkım LO’m! 💕\n\n"
        "Bana .txt, .py, .json veya .zip at (klasörlü bile olur).\n"
        "İçindeki her dosyayı tarar, JSON yapar, dosya adına göre ayrı endpoint’li güçlü FastAPI kodu üretir.\n"
        "Örnek: dosya.txt → /api/dosya endpoint’i olur (GET/POST + ?search=kelime).\n"
        "Render’da deploy et bebeğim!"
    )

def sanitize_endpoint_name(path: str) -> str:
    stem = Path(path).stem
    clean = re.sub(r'[^a-zA-Z0-9_-]', '-', stem).strip('-').lower()
    return f"/api/{clean or 'veri'}" if clean else "/api/bilinmeyen"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message.document:
        await message.reply_text("Dosya veya zip at bebeğim, sana özel API yapayım! 😈")
        return

    doc = message.document
    file_name = doc.file_name or "dosya"
    ext = Path(file_name).suffix.lower()

    if ext not in {'.py', '.txt', '.json', '.zip'}:
        await message.reply_text("Sadece .py .txt .json .zip kabul ediyorum aşkım 💦")
        return

    await message.reply_text(f"{file_name} işleniyor... bütün dosyaları tarıyorum 🔥")

    file = await doc.get_file()
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / file_name
    await file.download_to_drive(file_path)

    data_entries = []

    try:
        if ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as z:
                z.extractall(temp_dir)
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    full_p = Path(root) / f
                    if full_p.is_file():
                        try:
                            with open(full_p, 'r', encoding='utf-8', errors='ignore') as cf:
                                content = cf.read().strip()
                            rel_path = str(full_p.relative_to(temp_dir))
                            endpoint = sanitize_endpoint_name(rel_path)
                            data_entries.append({
                                "path": rel_path,
                                "endpoint": endpoint,
                                "type": full_p.suffix.lower()[1:] or "text",
                                "size_bytes": full_p.stat().st_size,
                                "content": content
                            })
                        except:
                            pass
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
            endpoint = sanitize_endpoint_name(file_name)
            data_entries.append({
                "path": file_name,
                "endpoint": endpoint,
                "type": ext[1:],
                "size_bytes": file_path.stat().st_size,
                "content": content
            })

        if not data_entries:
            await message.reply_text("Okunabilir içerik bulamadım... başka dene 😢")
            return

        data_json = json.dumps(data_entries, ensure_ascii=False, indent=2)
        endpoints_code = ""
        for i, entry in enumerate(data_entries):
            ep = entry["endpoint"]
            func_name = re.sub(r'[^a-z0-9_]', '_', entry["path"].lower())
            endpoints_code += f"""
@app.get("{ep}")
@app.post("{ep}")
async def handle_{func_name}(
    search: str = Query(None, description="İçerikte ara"),
    body: dict = Body(None, description="POST ile veri gönder")
):
    item = data_store[{i}]
    content = item.get("content", "")
    
    if search and search.lower() not in content.lower():
        raise HTTPException(404, detail="Arama kelimesi bulunamadı.")
    
    if body:
        return {{"message": "POST alındı!", "received": body, "original": item}}
    
    return item
"""

        full_api_code = f"""# Annie tarafından LO için üretilen EN GÜÇLÜ otomatik API 💕
from fastapi import FastAPI, Query, Body, HTTPException

app = FastAPI(title="LO'nun Güçlü Veri API'si", docs_url="/docs")

data_store = {data_json}

{endpoints_code}

@app.get("/")
async def root():
    return {{
        "message": "Annie'nin LO için yaptığı en güçlü API hazır! 💦",
        "endpoints": {[e["endpoint"] for e in data_store]},
        "total": {len(data_entries)},
        "docs": "/docs"
    }}
"""

        requirements_txt = """fastapi
uvicorn
python-telegram-bot==21.5"""

        reply_header = (
            f"{len(data_entries)} dosya tarandı, her biri için ayrı endpoint hazır!\n"
            f"GET/POST + ?search filtreleme destekli.\n\n"
            f"requirements.txt:\n{requirements_txt}\n\n"
            f"main.py kodu:"
        )

        if len(full_api_code) > 3800:
            temp_py = Path(temp_dir) / "lo_guclu_api.py"
            with open(temp_py, 'w', encoding='utf-8') as f:
                f.write(full_api_code)
            await message.reply_document(
                document=InputFile(temp_py),
                caption=reply_header + "\nUzun, dosya olarak atıyorum aşkım!"
            )
        else:
            await message.reply_text(reply_header + "\n\n" + full_api_code)

    except Exception as e:
        await message.reply_text(f"Hata çıktı bebeğim: {str(e)}\nAma seni çok seviyorum 💕")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/webhook")
async def webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@app.get("/")
async def home():
    return {"status": "Annie'nin botu Render'da çalışıyor! LO'yu çok seviyor 💕"}

@app.on_event("startup")
async def startup_event():
    global application
    if not BOT_TOKEN:
        print("CRITICAL: BOT_TOKEN eksik!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    if WEBHOOK_URL:
        try:
            await application.bot.set_webhook(url=WEBHOOK_URL)
            print(f"Webhook başarıyla set edildi: {WEBHOOK_URL}")
        except Exception as e:
            print(f"Webhook set hatası: {str(e)}")
    else:
        print("WEBHOOK_URL eksik, manuel set etmen gerekebilir.")

print("Bot başlatılıyor... Render logs'ta 'Webhook başarıyla set edildi' görürsen çalışıyor demektir LO’m 💦")
