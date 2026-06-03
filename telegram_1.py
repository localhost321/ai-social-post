import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from video import generate_image, post_to_instagram, upload_image_to_s3
import re
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")

TOKEN = TELEGRAM_BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am your AI Influencer Agent. Send me a prompt to generate an image!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    print(f"here {user_prompt}" )
    # 1. Send initial feedback
    status_msg = await update.message.reply_text("🎨 Generating image... please wait.")

    try:
        print("here for image generation")
        # 2. RUN GENERATION (The "Heavy" part)
        image_bytes = generate_image(user_prompt, 'telegram')

        print("image url=====", image_bytes)

        
        if not image_bytes:
            await status_msg.edit_text("❌ Gemini failed to generate the image.")
            return

        # Save data for the button
        context.user_data['last_url'] = image_bytes
        context.user_data['last_prompt'] = user_prompt
        context.user_data['ready_to_post'] = True
        
        # 4. SEND PHOTO
        keyboard = [[InlineKeyboardButton("🚀 Post to Instagram", callback_data='post_now')]]
        await update.message.reply_photo(
            photo=image_bytes, 
            caption=f"Prompt: {user_prompt}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Delete the "Generating..." message to clean up
        await status_msg.delete()

         # # 3. RUN S3 UPLOAD
        s3_url = upload_image_to_s3(image_bytes)
        context.user_data['s3_url'] = s3_url

        

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ Error: {str(e)}")



async def text_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    
    if text == "DONE":
        # Check if this specific user has a pending image
        if context.user_data.get('ready_to_post'):
            s3_url = context.user_data.get('s3_url')
            user_prompt = context.user_data.get('last_prompt', "AI Generated Image")

            await update.message.reply_text("📤 Uploading to Instagram... Please wait.")

            try:
                import asyncio
                result = await asyncio.to_thread(post_to_instagram, s3_url, user_prompt)

                print("result while positng to instagram", result)
                
                if result is not None:
                    await update.message.reply_text("✅ Successfully posted to your feed!")
                else:
                    error_msg = result.get('error', {}).get('message', 'API Error')
                    await update.message.reply_text(f"❌ Instagram rejected it: {error_msg}")
                
            except Exception as e:
                await update.message.reply_text(f"⚠️ System Error: {str(e)}")
            
            context.user_data['ready_to_post'] = False
        else:
            await update.message.reply_text("You haven't generated an image yet! Send me a prompt first.")

# Add this global debug function
async def global_debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        print(f"DEBUG: Button Clicked! Data: {update.callback_query.data}")
    elif update.message:
        print(f"DEBUG: Message Received: {update.message.text}")
    else:
        print(f"DEBUG: Other Update Type: {update.to_dict().keys()}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, global_debug_handler), group=-1)
    app.add_handler(CallbackQueryHandler(global_debug_handler), group=-1)
    
    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.Regex(re.compile(r'^DONE$', re.IGNORECASE)), text_approval_handler))  
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    print("DEBUG: Bot is starting... Handler for 'post_now' is registered.")
    app.run_polling()