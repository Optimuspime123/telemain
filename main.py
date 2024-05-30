import os
os.system("pip uninstall telegram")
os.system("pip install python-telegram-bot==13.2")
import base64
import re
import time
import urllib3
import requests
import json
import telegram
from openai import OpenAI
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

BOT_TOKEN = "7021728236:AAFIeC30KNlJ2V8QFDJ8OegnxltCJ0YN29U"  #notestbot
anyscale_client = OpenAI(base_url="https://api.endpoints.anyscale.com/v1",api_key="esecret_r5x1g895b4cfe2rlp4cjylmf7d")
oai_client = OpenAI(api_key="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",base_url="https://gateway.ai.cloudflare.com/v1/862c59c85be413ee9a09c1b8a84c59ba/optimus/openai")
updater = Updater(token=BOT_TOKEN, use_context=True, workers=12)
dispatcher = updater.dispatcher


def encode_image(image_path):
    """Encodes an image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def start(update, context):
    """Sends welcome message and image on /start command."""
    user = update.effective_user
    welcome_message = f"👋 Hi {user.first_name}, welcome to Cogify, an advanced AI-bot powered by GPT-4o and DALL·E 3! 🤖✨\n \n 💬 Send me a message to get started! I'm happy to chat, answer questions, help with analysis and writing tasks, and more.\n \n 🖼️ Type '/img [your prompt]' to generate images using DALL·E 3. For example: /img a majestic lion on the African savanna at sunset, digital art \n \n 🏞️ Send any image and I'll use GPT-4 with computer vision to analyze and discuss it with you.\n \n 🧹 If you ever want to clear our conversation history and start fresh, just type '/clear' \n\n Start a prompt with /web to give GPT-4 access to information from the web! (works best with gpt-4-turbo) \n\n Use /settings to change bot settings. \n\n ℹ️ Learn more about what I can do at https://cogify.social \n "

    try:
        context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                     action=ChatAction.TYPING)
    except Exception as e:
        print(
            f"Error occurred while sending chat action: {str(e)}. Retrying in 2 seconds..."
        )
        time.sleep(2)
        try:
            context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                         action=ChatAction.TYPING)
        except Exception as e:
            print(
                f"Error occurred again while sending chat action: {str(e)}. Skipping."
            )
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="https://graph.org/file/fd41b5e034a27cc4d65b6.jpg",
        caption=welcome_message,
        reply_to_message_id=update.message.message_id)


def filter_response(response):
    filtered_response = {}

    # Filter for timezone information
    if 'timeZone' in response:
        filtered_response['timeZone'] = {}
        if 'primaryCityTime' in response['timeZone']:
            filtered_response['timeZone']['primaryCityTime'] = {
                key: value for key, value in response['timeZone']['primaryCityTime'].items() if key != 'utcOffset'
            }

    # Filter for relevant web pages
    if 'webPages' in response and 'value' in response['webPages']:
        filtered_response['webPages'] = {'value': []}
        for page in response['webPages']['value']:
            filtered_page = {
                'name': page.get('name', ''),
                'url': page.get('url', ''),
                'snippet': page.get('snippet', '')
            }
            # Keep only relevant fields
            if 'displayUrl' in page:
                filtered_page['displayUrl'] = page.get('displayUrl', '')
            if 'dateLastCrawled' in page:
                filtered_page['dateLastCrawled'] = page.get('dateLastCrawled', '')
            filtered_response['webPages']['value'].append(filtered_page)

    # Filter for relevant news
    if 'news' in response and 'value' in response['news']:
        filtered_response['news'] = {'value': []}
        for article in response['news']['value']:
            filtered_article = {
                'name': article.get('name', ''),
                'url': article.get('url', ''),
                'description': article.get('description', ''),
                'datePublished': article.get('datePublished', '')
            }
            # Keep only relevant fields
            if 'provider' in article:
                filtered_article['provider'] = article.get('provider', '')
            if 'category' in article:
                filtered_article['category'] = article.get('category', '')
            filtered_response['news']['value'].append(filtered_article)

    # Filter for relevant videos
    if 'videos' in response and 'value' in response['videos']:
        filtered_response['videos'] = {'value': []}
        for video in response['videos']['value']:
            filtered_video = {
                'name': video.get('name', ''),
                'description': video.get('description', ''),
                'url': video.get('contentUrl', ''),
                'datePublished': video.get('datePublished', ''),
                'publisher': video.get('publisher', '')
            }
            filtered_response['videos']['value'].append(filtered_video)

    return filtered_response
    
def search(query):
    # Construct a request
    mkt = 'en-US'
    params = {
        'q': query,
        'mkt': mkt,
        'safeSearch': 'Off',
        'count': 3,
        'answerCount': 3
    }
    headers = {'Ocp-Apim-Subscription-Key': "047963dcb4aa4d558018b3dcec09a3af"}
    bing_search_endpoint = "https://api.bing.microsoft.com/v7.0/search"
    
    # Call the API
    try:
        response = requests.get(bing_search_endpoint, headers=headers, params=params)
        response.raise_for_status()
        json_response = response.json()
        
        # Remove unwanted keys
        keys_to_remove = ['spellSuggestions', 'relatedSearches', 'rankingResponse']
        filtered_response = {key: value for key, value in json_response.items() if key not in keys_to_remove}
        
        # Further filter the response
        filtered_response = filter_response(filtered_response)
        
        print(json.dumps(filtered_response, indent=2))
        return filtered_response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None



def settings(update, context):
    """Shows current settings and sends inline keyboard buttons to choose settings to modify."""
    model = context.user_data.get("model", "Default - gpt-4o")
    quality = context.user_data.get("quality", "standard")
    sys_prompt = context.user_data.get("sys_prompt", "Default")

    current_settings = f"Current settings:\n\n🤖 Default model: {model}\n🖼️ Generation quality: {quality}\n✨ System prompt: {sys_prompt}\n"

    keyboard = [[
        InlineKeyboardButton(" 🖼️ Generation quality",
                             callback_data="generation_quality")
    ], [
        InlineKeyboardButton("✨ System prompt", callback_data="system_prompt")
    ], [
        InlineKeyboardButton(" 🤖Default model", callback_data="default_model")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(current_settings + "Choose which setting you wish to modify:",
                              reply_markup=reply_markup,
                              reply_to_message_id=update.message.message_id)



def settings_callback(update, context):
    """Handles the settings callback and updates the respective setting."""
    query = update.callback_query
    setting = query.data

    if setting == "generation_quality":
        keyboard = [[
            InlineKeyboardButton("Standard", callback_data="standard")
        ], [InlineKeyboardButton("HD", callback_data="hd")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Choose image generation quality:",
                                reply_markup=reply_markup)
    elif setting == "system_prompt":
        query.edit_message_text(
            "Send your custom system prompt and remember to /clear conversation history for the changes to take effect!"
        )
        context.user_data["awaiting_sys_prompt"] = True
    elif setting == "default_model":
        keyboard = [[
            InlineKeyboardButton("GPT-4-Turbo", callback_data="gpt-4-turbo")
        ], [InlineKeyboardButton("GPT-4o", callback_data="gpt-4o")],[InlineKeyboardButton("Llama-3-70b", callback_data="llama-3")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Choose default model for making requests:",
                                reply_markup=reply_markup)

    query.answer()


def generation_quality_callback(update, context):
    """Handles the generation quality callback and stores the chosen quality."""
    query = update.callback_query
    quality = query.data
    context.user_data["quality"] = quality
    query.answer()
    query.edit_message_text(f"Image generation quality set to: {quality}")


def default_model_callback(update, context):
    """Handles the default model callback and stores the chosen model."""
    query = update.callback_query
    model = query.data
    context.user_data["model"] = model
    query.answer()
    query.edit_message_text(f"Default model set to: {model}")


def llama_response(update, context):
    messages = context.user_data.get("messages", [])
    # Remove any message with type: image_url
    messages = [msg for msg in messages if not (isinstance(msg["content"], list) and any("image_url" in part for part in msg["content"]))]
    context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                         action=ChatAction.TYPING)
    response = anyscale_client.chat.completions.create(
        model='meta-llama/Meta-Llama-3-70B-Instruct',
        messages=messages.copy(),
        stream=False,
        max_tokens=2000
    )

    return response.choices[0].message.content

def respond_to_message(update, context):
    """Handles user text and image messages, sends to OpenAI."""
    try:
        user = update.effective_user
        message = update.message
        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '', user.first_name or '')

        # Check if the user is awaiting a system prompt
        if context.user_data.get("awaiting_sys_prompt"):
            context.user_data["sys_prompt"] = message.text
            context.user_data["awaiting_sys_prompt"] = False
            update.message.reply_text(
                "System prompt set. Remember to /clear conversation history for the changes to take effect.",
                reply_to_message_id=update.message.message_id)
            return

        # Store message history with initial system message
        if "messages" not in context.user_data:
            context.user_data["messages"] = []

        # Check if a message with the role "system" already exists
        system_prompt_exists = any(msg["role"] == "system"
                                   for msg in context.user_data["messages"])

        if not system_prompt_exists:
            # Append the system prompt if it doesn't exist
            system_prompt = context.user_data.get(
                "sys_prompt",
                f"You are Cogify, an advanced Telegram AI bot built to help users. You can process text and image inputs using the GPT-4 model, and can generate images using DALL-E3 - command is /img "
                "{prompt}"
                ". Be friendly and helpful! The user's first name is {sanitized_name} or 'the user' , use it sparingly in conversation. More information about your developer can be found by the user at https://cogify.social , promote it only if user asks for info about yourself. to clear conversation history user should send /clear. To choose settings they can send /settings . To get results from the internet they can use /web {query}  "
            )
            context.user_data["messages"].append({
                "role": "system",
                "content": system_prompt
            })

        # Check the number of characters in the messages array
        total_characters = sum(
            len(msg["content"]) for msg in context.user_data["messages"])

        # If the total characters exceed 60,000, clear the messages array
        if total_characters > 20000:
            context.user_data["messages"] = []

        # Check if a new /web command is used
        if message.text and message.text.startswith("/web "):
            query = message.text[5:]  # Remove "/web " to isolate the search query

            placeholder_message = context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Searching the web... this can take a while",
                reply_to_message_id=update.message.message_id)
            context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                         action=ChatAction.TYPING)

            json_results = search(query)
            system_message = f"The user requested a web search, here are the results: {json_results}. You are advised to use them in your response and cite sources if relevant . "
            context.user_data["messages"].append({
                "role": "system",
                "content": system_message
            })

            context.user_data["messages"].append({
                "role": "user",
                "content": query
            })

        else:
            # Handle text messages
            if message.text:
                context.user_data["messages"].append({
                    "role": "user",
                    "content": message.text
                })

                # Check if the selected model is llama-3 and call llama_response
                if context.user_data.get("model") == "llama-3":
                    context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                         action=ChatAction.TYPING)
                    llama_reply = llama_response(update, context)
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=llama_reply)
                    return

            # Handle image messages
            elif message.photo:
                model = context.user_data.get("model", "gpt-4o")
                if model not in ["gpt-4-turbo", "gpt-4o"]:
                    context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Your chosen model does not support images as input. Please send a text message or switch models from /settings.",
                    reply_to_message_id=update.message.message_id
                    )
                    return
                # Download the largest photo size
                file_id = message.photo[-1].file_id
                newFile = context.bot.get_file(file_id)
                newFile.download('temp_image.jpg')

                # Encode the image to base64
                base64_image = encode_image('temp_image.jpg')
                os.remove('temp_image.jpg')  # Clean up the temporary image file

                context.user_data["messages"].append({
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": message.caption or "User has uploaded this image: "
                    }, {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }]
                })

            # Send placeholder message
            placeholder_message = context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please wait... this can take a while",
                reply_to_message_id=update.message.message_id)
            context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                         action=ChatAction.TYPING)

        messages = context.user_data["messages"]

        # Get the selected model from user data, default to "gpt-4o" if not set
        model = context.user_data.get("model", "gpt-4o")
        response = oai_client.chat.completions.create(model=model,
                                                  messages=messages.copy(),
                                                  max_tokens=2024,
                                                  stream=False)

        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=placeholder_message.message_id,
            text=response.choices[0].message.content,
            parse_mode=telegram.ParseMode.MARKDOWN)
        #print(response.choices[0].message.content)
        # Store assistant's response
        context.user_data["messages"].append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })

    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Sorry , An error occurred: {str(e)} You can try to switch to a different model from /settings")



def clear_history(update, context):
    """Clears the message history for the user."""
    context.user_data["messages"] = []
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Conversation history has been cleared.",
                             reply_to_message_id=update.message.message_id)


def generate_image(update, context):
    """Generates an image using DALL-E 3 based on the provided prompt."""
    try:
        prompt = ' '.join(context.args)
        if not prompt:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please provide a prompt after the /img command.")
            return

        placeholder_message = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Generating image... this can take a while",
            reply_to_message_id=update.message.message_id)
        context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                     action=ChatAction.UPLOAD_PHOTO)

        # Get the selected quality from user data, default to "standard" if not set
        quality = context.user_data.get("quality", "standard")

        response = oai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality=quality,
            n=1,
        )

        image_url = response.data[0].url
        context.bot.delete_message(chat_id=update.effective_chat.id,
                                   message_id=placeholder_message.message_id)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=image_url,
                               caption=prompt,
                               reply_to_message_id=update.message.message_id)
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"An error occurred: {str(e)}")


def report_error(exception):
    error_message = f"Request error: {str(exception)}. Restarting the bot."
    chat_id = "1218619440"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": error_message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send error report: {str(e)}")

def no_generate_image(update, context):
    """Informs the user that image generation is unavailable."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Image generation is currently unavailable for this bot. Try it out at https://cogify.social/image",
        reply_to_message_id=update.message.message_id
    )

dispatcher.add_handler(CommandHandler("clear", clear_history, run_async=True))
dispatcher.add_handler(CommandHandler("start", start, run_async=True))
dispatcher.add_handler(CommandHandler("img", generate_image, run_async=True))
dispatcher.add_handler(CommandHandler("img1", generate_image, run_async=True))
dispatcher.add_handler(CommandHandler("settings", settings))
dispatcher.add_handler(
    CallbackQueryHandler(
        settings_callback,
        pattern="^(generation_quality|system_prompt|default_model)$"))
dispatcher.add_handler(
    CallbackQueryHandler(generation_quality_callback,
                         pattern="^(standard|hd)$"))
dispatcher.add_handler(
    CallbackQueryHandler(default_model_callback,
                         pattern="^(gpt-4-turbo|gpt-4o|llama-3|mixtral|claude)$"))

dispatcher.add_handler(
    MessageHandler(Filters.text | Filters.photo, respond_to_message, run_async=True))

# Start the bot with error handling
while True:
    try:
        updater.start_polling()
        updater.idle()
    except Exception as e:
        report_error(e)
        # Restart the bot after a short delay
        time.sleep(5)
