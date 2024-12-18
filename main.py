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
pplx_client = OpenAI(api_key="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",base_url="https://api.perplexity.ai",)
#oai_client = OpenAI(api_key="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",base_url="https://gateway.ai.cloudflare.com/v1/862c59c85be413ee9a09c1b8a84c59ba/optimus/openai")
part_a = "sk-proj-FFjyhUaYXN"
part_b = "-916RB1LPIr6RE15aS18ChOqlGq97agNit37"
part_c = "51OPorQHHtga7a3rpWi14ZBoGs8UT3BlbkFJRAPjdqqbLjxEr0NXEyf8fJP7EHX1mcv8hyqhhszHHvia5QeWJRFOJb-1s9ilJa-tHMdM32_aMA"

oai_client = OpenAI(api_key=part_a + part_b + part_c)
any_client = OpenAI(api_key="meowmeow69",base_url="https://api.airforce")
#fresed_client = OpenAI(base_url="https://fresedgpt.space/v1", api_key="fresed-aRxFAtH4C1u93VN0G7E59CaHw9L6V2")

updater = Updater(token=BOT_TOKEN, use_context=True, workers=12)
dispatcher = updater.dispatcher


def encode_image(image_path):
    """Encodes an image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def start(update, context):
    """Sends welcome message and image on /start command."""
    user = update.effective_user
    welcome_message = f"👋 Hi {user.first_name}, welcome to Cogify, an advanced AI-bot powered by GPT-4o and DALL·E 3! 🤖✨\n \n 💬 Send me a message to get started! I'm happy to chat, answer questions, help with analysis and writing tasks, and more.\n \n 🖼️ Type '/img [your prompt]' to generate images using DALL·E 3. For example: /img a majestic lion on the African savanna at sunset, digital art \n \n 🏞️ Send any image and I'll use GPT-4 with computer vision to analyze and discuss it with you.\n \n 🧹 If you ever want to clear our conversation history and start fresh, just type '/clear' \n\n Start a prompt with /web to get responses from web-enabled llama3.1 by perplexity \n\n Use /settings to change bot settings. \n\n ℹ️ Learn more about what I can do at https://cogify.social \n "

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
            InlineKeyboardButton("DALL-E 3 - Standard", callback_data="standard")
        ], [
            InlineKeyboardButton("DALL-E 3 - HD", callback_data="hd")
        ], [
            InlineKeyboardButton("Flux", callback_data="flux")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Choose image generation quality:",
                                reply_markup=reply_markup)
    elif setting == "system_prompt":
        query.edit_message_text(
            "Send your custom system prompt and remember to /clear conversation history for the changes to take effect!"
        )
        context.user_data["awaiting_sys_prompt"] = True
    elif setting == "default_model":
        keyboard = [
            [InlineKeyboardButton("GPT-4o", callback_data="gpt-4o")],
            [InlineKeyboardButton("Llama3.1-70b Online", callback_data="llama-3.1-sonar-large-128k-online")],
            [InlineKeyboardButton("Llama3.1-8b Online", callback_data="llama-3.1-sonar-small-128k-online")],
            [InlineKeyboardButton("Mixtral - ⚠", callback_data="mixtral-8x7b-instruct")]
        ]
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


def pplx_response(update, context):
    messages = context.user_data.get("messages", [])
    model = "llama-3.1-sonar-small-128k-online"  # Retrieve model or use default
    
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    response = pplx_client.chat.completions.create(
        model=model,
        messages=messages.copy(),
        stream=False,
        max_tokens=2000
    )
    message_content = response.choices[0].message.content

    # Extract citation URLs directly
    citation_urls = response.citations  # This is already a list of URLs

    # Format citation URLs for display
    if citation_urls:
        citation_text = "\n\nRead more at:\n" + "\n".join(
            [f"- {url}" for url in citation_urls]
        )
    else:
        citation_text = ""

    # Combine the message content and citation links
    pplx_response_text = message_content + citation_text

    return pplx_response_text


def anyAI_response(update, context):
    messages = context.user_data.get("messages", [])
    
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    response = any_client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        messages=messages.copy(),
        stream=False,
        max_tokens=4000
    )
    
    return response.choices[0].message.content


def respond_to_message(update, context):
    """Handles user text and image messages, sends for inference."""
    try:
        user = update.effective_user
        message = update.message
        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '', user.first_name or ' ')

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
                f"You are Cogify, an advanced Telegram AI bot built to help users. You can process text (and image inputs using the GPT-4o model), and can generate images using DALL-E3 - command is /img "
                "{prompt}"
                ". Be friendly and helpful!  to clear conversation history user should send /clear. To choose settings and change AI Model used they can send /settings . To get results from the internet they can use /web {query}  "
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

        # Handle text messages
        if message.text:
            context.user_data["messages"].append({
                "role": "user",
                "content": message.text
            })
            
            if message.text.startswith("/web "):
                context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                             action=ChatAction.TYPING)
                pplx_reply = pplx_response(update, context)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=pplx_reply, parse_mode=telegram.ParseMode.MARKDOWN)
                context.user_data["messages"].append({
                    "role": "assistant",
                    "content": pplx_reply
                })        
                return

            

            # Check if the selected model is not gpt-4o and call pplx_response
            model = context.user_data.get("model", "gpt-4o")
            if model in ["llama-3.1-sonar-large-128k-online", "llama-3.1-sonar-small-128k-online"]:
                context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                             action=ChatAction.TYPING)
                pplx_reply = pplx_response(update, context)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=pplx_reply, parse_mode=telegram.ParseMode.MARKDOWN)
                context.user_data["messages"].append({
                    "role": "assistant",
                    "content": pplx_reply
                })        
                return
            elif model == "claude-3-5-sonnet-20240620":
                context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                             action=ChatAction.TYPING)
                anyAI_reply = anyAI_response(update, context)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=anyAI_reply, parse_mode=telegram.ParseMode.MARKDOWN)
                context.user_data["messages"].append({
                    "role": "assistant",
                    "content": anyAI_reply
                })        
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
                                 text=f"Sorry, An error occurred: {str(e)}. You can try to switch to a different model from /settings.")


def clear_history(update, context):
    """Clears the message history for the user."""
    context.user_data["messages"] = []
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Conversation history has been cleared.",
                             reply_to_message_id=update.message.message_id)


def getfluximage(prompt):
    """Generates an image using flux based on the provided prompt."""
    try:
        url = f"https://api.airforce/imagine2?model=Flux&prompt={prompt}"
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise RuntimeError(f"Failed to generate image with flux: {str(e)}")


def generate_image(update, context):
    """Generates an image using DALL-E 3 or flux based on the provided prompt."""
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

        if quality == "flux":
            image_data = getfluximage(prompt)
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=placeholder_message.message_id)
            context.bot.send_photo(chat_id=update.effective_chat.id,
                                   photo=image_data,
                                   caption=prompt,
                                   reply_to_message_id=update.message.message_id)
        else:
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
                         pattern="^(standard|hd|flux)$"))
dispatcher.add_handler(
    CallbackQueryHandler(default_model_callback,
                         pattern="^(gpt-4o|llama-3.1-sonar-large-128k-online|llama-3.1-sonar-small-128k-online|mixtral-8x7b-instruct)$"))

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
