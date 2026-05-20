import time
import requests
import google.generativeai as genai
from PIL import Image
from instagrapi import Client
import requests
import os
import time

# --- CONFIGURATION ---
GEMINI_KEY = "AIzaSyBjp9fs6xFpk5l8o0z3UF009bnD5b2Q_ws"
KLING_API_KEY = "7d99af24-16a6-4c60-8e97-2b826b7428b1:e36bd0f303bc0772dc186160b293ef6e" # Using AI/ML API for Kling v1
IG_USERNAME = "traveller_bandar"
IG_PASSWORD = "Deepu@1234"


# instagram app id: 2669200206795188
# instagram app secret : 23db7c6e70c079c0480b8c8e35de633e

INSTA_USER_ID=17841431818580983

# shot lived instagram token
# INSTA_ACCESS_TOKEN="EAAYTTQhSZBnABRYkPUtqDLafZB6LmHCS5wDBKqqeqKoHqY7J8okZBXVlq2X72ZCEZCUELa8RbxIvHZA3VStEJGHxRIZBTyYkASZBSiP38CmF4WIZB67vI1uvZBFIhApkrDOOYfr1P17pZCoGMducVjtWsRHqwYJoQrPnuFGNReD9jyZCK2ZCCECuzZCY4gy5sSZARqZCkQ3PWpgjo4BK4xLNrTrxkNBaS4SMHCcud8fu0wAXLs4j9zLwquQyCvBcUT1VeoxgQeztkyTRoRbp57WvLAmYBV0h"

# 60 days live instagram token
INSTA_ACCESS_TOKEN="EAAYTTQhSZBnABRSxTdUuZBqBSsTnAbWWIsldZAGLW9RAcDAcheMdO9IyntY3onRAvlofRwU79VuH48mpa7oDxDYMz48kNEojT3VlpaJZBeBYEBim13HVxU4DoLX1ZCt9H5PqB82yvUZAthXPyMCafZCutYG7VP6flIKCjvZAS5eOeuPZAfZA5trZBZBllnGYTpY7WrrW"
import os
os.environ["FAL_KEY"] = KLING_API_KEY

# --- SETUP GEMINI ---
genai.configure(api_key=GEMINI_KEY)
BUCKET_NAME = "aisocialbucket"


import os
import boto3
from datetime import datetime

def upload_image_to_s3(image_bytes):
    # Dynamic key to prevent overwriting
    file_key = f"image_1.png"
    
    s3 = boto3.client('s3')
    
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=image_bytes,
            ContentType='image/png',     
            ACL='public-read'
        )
        
        # Generate the URL
        region = 'ap-south-1'
        bucket_name = BUCKET_NAME
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}"
        
        return url
    

    except Exception as e:
        print(f"S3 Upload Error: {e}")
        return None

# 1. GENERATE IMAGE
def generate_image(prompt, source):
    try:
        print("here in this funtion to generate image")
        model = genai.GenerativeModel("gemini-3.1-flash-image-preview")

        response = model.generate_content(
            prompt,
            generation_config={"response_modalities": ["IMAGE"]}
        )
        print("response for generatein gimage", response)

        image_bytes = response.candidates[0].content.parts[0].inline_data.data
        if source == 'telegram':
            return image_bytes
        public_url = upload_image_to_s3(image_bytes)
        if public_url:
            print(f"Ready to post to Instagram! URL: {public_url}")


        return public_url

    except Exception as e:
        print("Image generation error:", e)
        return None


# 2. POST TO INSTAGRAM


def post_to_instagram(image_url, caption):
    # Credentials from your environment
    ACCESS_TOKEN = INSTA_ACCESS_TOKEN
    IG_USER_ID = INSTA_USER_ID # Your Instagram Business Account ID
    
    base_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}"

    # STEP 1: Create the Media Container
    container_payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    
    response = requests.post(f"{base_url}/media", data=container_payload)
    print("response to post instagram", response)
    result = response.json()
    
    if 'id' not in result:
        print(f"Error creating container: {result}")
        return None

    creation_id = result['id']
    print(f"Container created! ID: {creation_id}")

    # OPTIONAL: Wait a few seconds for Instagram to process the image
    time.sleep(5)

    # STEP 2: Publish the Container
    publish_payload = {
        'creation_id': creation_id,
        'access_token': ACCESS_TOKEN
    }
    
    publish_response = requests.post(f"{base_url}/media_publish", data=publish_payload)
    publish_result = publish_response.json()
    
    if 'id' in publish_result:
        print(f"Success! Post Live ID: {publish_result['id']}")
        return publish_result['id']
    else:
        print(f"Publishing failed: {publish_result}")
        return None
    


# --- EXECUTION ---
if __name__ == "__main__":

    # prompt = """
    # ultra realistic beautiful young european female influencer, 22 years old,
    # sharp jawline, glowing skin, long straight black hair,
    # wearing trendy streetwear, sitting in aesthetic modern cafe,
    # soft sunlight, DSLR quality, instagram style, 4k
    # """

    prompt= """Ultra-realistic portrait of a beautiful baby girl, around 1–2 years old, big playful eyes with a sparkling joyful expression, soft glowing skin, tiny delicate features, natural rosy cheeks, gentle smile visible in her eyes, looking slightly upward, soft curly hair, warm natural lighting, shallow depth of field, DSLR quality, 4k, highly detailed, photorealistic, soft pastel background, dreamy atmosphere, candid moment, innocence and happiness captured"""

    print("🎨 Generating Image...")
    image_file = generate_image(prompt, 'script')

    if image_file:
        print("📸 Posting to Instagram...")
        caption = "Coffee vibes ☕✨ #AIinfluencer #aigirl #instagram"
        post_to_instagram(image_file, caption)




# instagram app id: 2669200206795188
# instagram app secret : 23db7c6e70c079c0480b8c8e35de633e

# accoutnid: 17841431818580983
# access token: IGAAl7n5opEbRBZAFoxc0U1WnY0UG1KTWJtNjRsVDB1cTBlUERkd180QTFTcENPa0RTTEE0ZAm1PTUY5ekRzTmlzMnc3cFlvTTBjaE9WbzRSRF83ckVhdUxNc09hZAWVrT25qd1J6RlRlZAGdoY1VHWWF4Q3FtZAVJ4dUs0MGpyZAXU3QQZDZD





# nistagram access token generated through graph api exploreer - short lived tokne:
# EAAYTTQhSZBnABRYkPUtqDLafZB6LmHCS5wDBKqqeqKoHqY7J8okZBXVlq2X72ZCEZCUELa8RbxIvHZA3VStEJGHxRIZBTyYkASZBSiP38CmF4WIZB67vI1uvZBFIhApkrDOOYfr1P17pZCoGMducVjtWsRHqwYJoQrPnuFGNReD9jyZCK2ZCCECuzZCY4gy5sSZARqZCkQ3PWpgjo4BK4xLNrTrxkNBaS4SMHCcud8fu0wAXLs4j9zLwquQyCvBcUT1VeoxgQeztkyTRoRbp57WvLAmYBV0h



# 60 days expiery token:
# EAAYTTQhSZBnABRSxTdUuZBqBSsTnAbWWIsldZAGLW9RAcDAcheMdO9IyntY3onRAvlofRwU79VuH48mpa7oDxDYMz48kNEojT3VlpaJZBeBYEBim13HVxU4DoLX1ZCt9H5PqB82yvUZAthXPyMCafZCutYG7VP6flIKCjvZAS5eOeuPZAfZA5trZBZBllnGYTpY7WrrW

# https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=2669200206795188&client_secret=23db7c6e70c079c0480b8c8e35de633e&fb_exchange_token=EAAYTTQhSZBnABRYkPUtqDLafZB6LmHCS5wDBKqqeqKoHqY7J8okZBXVlq2X72ZCEZCUELa8RbxIvHZA3VStEJGHxRIZBTyYkASZBSiP38CmF4WIZB67vI1uvZBFIhApkrDOOYfr1P17pZCoGMducVjtWsRHqwYJoQrPnuFGNReD9jyZCK2ZCCECuzZCY4gy5sSZARqZCkQ3PWpgjo4BK4xLNrTrxkNBaS4SMHCcud8fu0wAXLs4j9zLwquQyCvBcUT1VeoxgQeztkyTRoRbp57WvLAmYBV0h