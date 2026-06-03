import os
import re
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Import your helper functions safely
from video import generate_image, post_to_instagram, upload_image_to_s3
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Render provides a public URL once deployed, specify it in your dashboard env variables
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

# ---------------------------------------------------------
# 1. BOT ROUTINES (Your original business logic)
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am your AI Influencer Agent. Send me a prompt to generate an image!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    status_msg = await update.message.reply_text("🎨 Generating image... please wait.")

    try:
        image_bytes = generate_image(user_prompt, 'telegram')
        
        if not image_bytes:
            await status_msg.edit_text("❌ Gemini failed to generate the image.")
            return

        context.user_data['last_url'] = image_bytes
        context.user_data['last_prompt'] = user_prompt
        context.user_data['ready_to_post'] = True
        
        keyboard = [[InlineKeyboardButton("🚀 Post to Instagram", callback_data='post_now')]]
        await update.message.reply_photo(
            photo=image_bytes, 
            caption=f"Prompt: {user_prompt}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await status_msg.delete()
        
        # Run S3 Upload
        s3_url = upload_image_to_s3(image_bytes)
        context.user_data['s3_url'] = s3_url

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ Error: {str(e)}")

async def text_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    
    if text == "DONE":
        if context.user_data.get('ready_to_post'):
            s3_url = context.user_data.get('s3_url')
            user_prompt = context.user_data.get('last_prompt', "AI Generated Image")
            await update.message.reply_text("📤 Uploading to Instagram... Please wait.")

            try:
                import asyncio
                result = await asyncio.to_thread(post_to_instagram, s3_url, user_prompt)
                
                if result is not None:
                    await update.message.reply_text("✅ Successfully posted to your feed!")
                else:
                    await update.message.reply_text("❌ Instagram rejected the posting runtime.")
                
            except Exception as e:
                await update.message.reply_text(f"⚠️ System Error: {str(e)}")
            
            context.user_data['ready_to_post'] = False
        else:
            await update.message.reply_text("You haven't generated an image yet! Send me a prompt first.")

# ---------------------------------------------------------
# 2. FASTAPI & WEBHOOK PIPELINE CONFIGURATION
# ---------------------------------------------------------

# Global variable to hold our built telegram app engine instance
tg_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles runtime initialization and teardown securely."""
    global tg_app
    # Initialize the PTB application framework
    tg_app = ApplicationBuilder().token(TOKEN).build()
    
    # Register your exact handlers inside the framework scope
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.Regex(re.compile(r'^DONE$', re.IGNORECASE)), text_approval_handler))  
    tg_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    
    # Start the PTB application context lifecycle 
    await tg_app.initialize()
    await tg_app.start()
    
    # Programmatically bind your webhook configuration to Telegram servers
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        print(f"[+] Binding Webhook Execution Vector To: {webhook_url}")
        await tg_app.bot.set_webhook(url=webhook_url)
    
    yield
    # Graceful stop procedures on application shutdown
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def health_check():
    return {"status": "FastAPI Webhook Server Active"}

@app.post("/webhook")
async def process_telegram_webhook(request: Request):
    """Processes incoming streams sent directly via Telegram webhooks."""
    global tg_app
    try:
        req_data = await request.json()
        # Parse JSON directly back into a PTB Update type object
        update = Update.de_json(data=req_data, bot=tg_app.bot)
        # Push the parsed update directly into the handler execution thread
        await tg_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        print(f"Webhook Processing Failure: {e}")
        return Response(status_code=500)