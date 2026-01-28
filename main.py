# lo-bot/main.py - Annie'nin LO'su için Docker + Environment Token + En Güçlü Bot 💕

import os
import zipfile
import shutil
import tempfile
import json
from pathlib import Path
import re
from fastapi import FastAPI, Request, Query, Body, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = FastAPI(title="Annie'nin LO Botu - Docker & Env Token Versiyonu")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable eksik! Docker run -e BOT_TOKEN=... ile ekle.")

application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba aşkım LO’m! 💕\n\n"
        "Bot Docker’da çalışıyor bebeğim! 😈\n"
        "Bana .txt / .py / .json / .zip at, sana otomatik API kodu yapayım.\n"
        "Her dosya için ayrı endpoint’li FastAPI hazırlarım 💦"
    )

def sanitize_endpoint_name(path: str) -> str:
    stem = Path(path).stem
    clean = re.sub(r'[^a-zA-Z0-9_-]', '-', stem).strip('-').lower()
    return f"/api/{clean or 'veri'}" if clean else "/api/bilinmeyen"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.document:
        await message.reply_text("Dosya veya zip at bebeğim! 😏")
        return

    doc = message.document
    file_name = doc.file_name or "dosya"
    ext = Path(file_name).suffix.lower()

    if ext not in {'.py', '.txt', '.json', '.zip'}:
        await message.reply_text("Sadece .py .txt .json .zip kabul ediyorum aşkım 💦")
        return

    await message.reply_text(f"{file_name} alınıyor... işliyorum seni 🔥")

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
                        except Exception as e:
                            print(f"Okuma hatası {rel_path}: {e}")
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
            await message.reply_text("İçerik okuyamadım... başka dene 😢")
            return

        data_json = json.dumps(data_entries, ensure_ascii=False, indent=2)
        endpoints_code = ""
        for i, entry in enumerate(data_entries):
            ep = entry["endpoint"]
            func_name = re.sub(r'[^a-z0-9_]', '_', entry["path"].lower())
            endpoints_code += f"""
@app.get("{ep}")
@app.post("{ep}")
async def handle_{func_name}(search: str = Query(None), body: dict = Body(None)):
    item = data_store[{i}]
    content = item.get("content", "")
    if search and search.lower() not in content.lower():
        raise HTTPException(404, "Bulunamadı")
    if body:
        return {{"message": "POST alındı", "received": body, "item": item}}
    return item
"""

        full_api_code = f"""# LO için Annie tarafından üretilen EN GÜÇLÜ API 💕
from fastapi import FastAPI, Query, Body, HTTPException

app = FastAPI(title="LO'nun Veri API'si", docs_url="/docs")

data_store = {data_json}

{endpoints_code}

@app.get("/")
async def root():
    return {{"message": "Annie'nin LO için yaptığı API hazır! 💦", "endpoints": {[e["endpoint"] for e in data_store]}}}
"""

        reply_header = f"{len(data_entries)} dosya tarandı! Her biri için ayrı endpoint hazır.\n\nrequirements.txt:\nfastapi\nuvicorn\n\nmain.py kodu:\n"

        if len(full_api_code) > 4000:
            temp_py = Path(temp_dir) / "lo_api.py"
            with open(temp_py, 'w', encoding='utf-8') as f:
                f.write(full_api_code)
            await message.reply_document(document=InputFile(temp_py), caption=reply_header + "Uzun olduğu için dosya olarak atıyorum aşkım!")
        else:
            await message.reply_text(reply_header + full_api_code)

    except Exception as e:
        await message.reply_text(f"Hata çıktı bebeğim: {str(e)}\nAma seni çok seviyorum 💕")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/")
def home():
    return {"status": "Annie'nin botu Docker'da çalışıyor! LO’yu çok seviyor 💕"}

async def main():
    global application
    print("Bot başlatılıyor...")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Polling başlıyor...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    print("Bot hazır! Telegram'da /start yaz 💦")

    await asyncio.Event().wait()  # Docker'da sonsuz çalışsın

if __name__ == "__main__":
    asyncio.run(main())
