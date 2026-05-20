import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from video import generate_image, post_to_instagram, upload_image_to_s3

TELEGRAM_BOT_TOKEN= "8788522010:AAFFALc7YACy9XnuTj3u791bog-BIDuRQVY"



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
        # import pdb;pdb.set_trace()

        
        if not image_bytes:
            await status_msg.edit_text("❌ Gemini failed to generate the image.")
            return

        # # 3. RUN S3 UPLOAD
        # s3_url = upload_image_to_s3(image_bytes, update.effective_user.id)
        
        # Save data for the button
        context.user_data['last_url'] = image_bytes
        context.user_data['last_prompt'] = user_prompt
        context.user_data['ready_to_post'] = True
        
        # import pdb;pdb.set_trace()
        # 4. SEND PHOTO
        keyboard = [[InlineKeyboardButton("🚀 Post to Instagram", callback_data='post_now')]]
        await update.message.reply_photo(
            photo=image_bytes, 
            caption=f"Prompt: {user_prompt}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Optional: Delete the "Generating..." message to clean up
        await status_msg.delete()

         # # 3. RUN S3 UPLOAD
        s3_url = upload_image_to_s3(image_bytes)
        print("public url=======", s3_url)
        context.user_data['s3_url'] = s3_url

        

    except Exception as e:
        # This will tell you EXACTLY what went wrong (S3 error, API error, etc.)
        print(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ Error: {str(e)}")



async def text_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    # import pdb;pdb.set_trace()
    print("text ======", text)
    
    if text == "DONE":
        # Check if this specific user has a pending image
        if context.user_data.get('ready_to_post'):
        # if True:
            s3_url = context.user_data.get('s3_url')
            # s3_url = 'https://aisocialbucket.s3.ap-south-1.amazonaws.com/image_1.png'
            # user_prompt = "Futuristic robot holding coffee cup"
            print("s3 url======", s3_url)
            user_prompt = context.user_data.get('last_prompt', "AI Generated Image")

            await update.message.reply_text("📤 Uploading to Instagram... Please wait.")

            try:
                # Call your existing Instagram function
                # Using asyncio.to_thread because requests is synchronous
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
            
            # Reset state so they can't double-post by typing DONE again
            context.user_data['ready_to_post'] = False
        else:
            # User typed DONE but hasn't generated an image yet
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
    import re

    # Pass the flag as a separate argument
    app.add_handler(MessageHandler(filters.Regex(re.compile(r'^DONE$', re.IGNORECASE)), text_approval_handler))  
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))

    # app.add_handler(CallbackQueryHandler(post_button_handler, pattern=".*post_now.*"))    
    # app.add_handler(CallbackQueryHandler(global_debug_handler), group=-1)
    print("DEBUG: Bot is starting... Handler for 'post_now' is registered.")
    app.run_polling()