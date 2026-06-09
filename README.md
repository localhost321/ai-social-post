#  AI Social Media Manager

This is an telegram AI bot that handels the user input prompt and generated high-fidelity output image on the telegram chat itself, and when directed to post on your instagram feed, it post it on you 
instagram live feed using Insta Graph API.

# TechStack
Python , Telegram Bot API, Gemini(LLM) API, AWS S3, InstaGraph API

# Command to Operate Telegram Bot
  1. /start: To start the telegram Bot
  2. Provide image prompt after that, it will generate AI image
  3. Done. : To post to your instagram feed

# Run Project
 1. Create Virutalenvironment for this project : python3 -m venv venv
 2. Activate Virtualenvironemnt : source venv/bin/activate
 3. Install all requirements: pip install -r requirements.txt
 4. Run the project: python3 telegram_1.py

# Working and Architecture

As soon as project starts running, it will run continously and do polling to check if there is any input on telgram bot, if yes, it will proceed accordingly as per command instruction.
With /start command, it will introduce itslef, as an AI Social Media Manager
With prompt instruction to generate image: It generates images using Gemini API and pass the generated image on the telegram bot
With done instruction: It will post to your live instagram feed using InstaGraph API



