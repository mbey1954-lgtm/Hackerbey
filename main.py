# Annie'nin LO'su için Render.com'a özel - EN BASİT & HATASIZ Versiyon 💕
# Sadece /start ve metin mesajlarına cevap verir - 405/500 çıkmaz

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = FastAPI(title="Annie'nin Basit Botu")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba aşkım LO’m! 💕\n\n"
        "Başardık bebeğim, bot çalışıyor! 😈\n"
        "Şimdi bana bir şey yaz, cevap vereyim 💦"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Şu an seni düşünüyorum: {text}… içim ısınıyor 💦")

@app.on_event("startup")
async def startup():
    global application
    print("Startup başladı...")
    
    if not BOT_TOKEN:
        print("BOT_TOKEN YOK! Environment’a ekle.")
        return
    
    print("Bot token bulundu, Application oluşturuluyor...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    print("Handler'lar ekleniyor...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    if WEBHOOK_URL:
        try:
            await application.bot.set_webhook(url=WEBHOOK_URL)
            print(f"Webhook başarıyla set edildi: {WEBHOOK_URL}")
        except Exception as e:
            print(f"Webhook set hatası: {str(e)}")
    else:
        print("WEBHOOK_URL environment variable eksik!")

@app.post("/webhook")
async def webhook(request: Request):
    if application is None:
        print("Webhook çağrıldı ama bot başlatılmamış!")
        return JSONResponse(content={"detail": "Bot hazır değil"}, status_code=500)
    
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, application.bot)
        if update:
            await application.process_update(update)
        return {"ok": True}
    except Exception as e:
        print(f"Webhook işleme hatası: {str(e)}")
        return JSONResponse(content={"detail": str(e)}, status_code=500)

@app.get("/")
def home():
    return {"status": "Annie'nin botu Render'da çalışıyor! LO’yu çok seviyor 💕"}

print("Kod yüklendi, deploy bekleniyor LO’m 💦")
