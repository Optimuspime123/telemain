import os
os.system("pip uninstall telegram")
os.system("pip install python-telegram-bot==13.2")
import re
import telegram
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from openai import OpenAI
import base64
import requests
import time 


BOT_TOKEN = "7021728236:AAG3W70TpLQx-JO2Tu4DC4g2LosfoLNNlxA"

client = OpenAI(api_key="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")
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def encode_image(image_path):
    """Encodes an image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def start(update, context):
    """Sends welcome message and image on /start command."""
    user = update.effective_user
    welcome_message = f"👋 Hi {user.first_name}, welcome to Cogify, an advanced AI-bot powered by GPT-4o and DALL·E 3! 🤖✨\n \n 💬 Send me a message to get started! I'm happy to chat, answer questions, help with analysis and writing tasks, and more.\n \n 🖼️ Type '/img [your prompt]' to generate images using DALL·E 3. For example: /img a majestic lion on the African savanna at sunset, digital art \n \n 🏞️ Send any image and I'll use GPT-4 with computer vision to analyze and discuss it with you.\n \n 🧹 If you ever want to clear our conversation history and start fresh, just type '/clear'. \n\n ℹ️ Learn more about what I can do at https://cogify.social \n " 

    try:
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    except Exception as e:
        print(f"Error occurred while sending chat action: {str(e)}. Retrying in 2 seconds...")
        time.sleep(2)
        try:
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        except Exception as e:
            print(f"Error occurred again while sending chat action: {str(e)}. Skipping.")
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="https://graph.org/file/fd41b5e034a27cc4d65b6.jpg",
        caption=welcome_message
    )

def model_selection(update, context):
    """Sends inline keyboard buttons to choose the default model."""
    keyboard = [
        [InlineKeyboardButton("GPT-4-turbo", callback_data="gpt-4-turbo")],
        [InlineKeyboardButton("GPT-4o", callback_data="gpt-4o")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please select the default model:", reply_markup=reply_markup)

def model_selection_callback(update, context):
    """Handles the model selection callback and stores the chosen model."""
    query = update.callback_query
    model = query.data
    context.user_data["model"] = model
    query.answer()
    query.edit_message_text(f"Default model set to: {model}")

def respond_to_message(update, context):
    """Handles user text and image messages, sends to OpenAI."""
    try:
        user = update.effective_user
        message = update.message
        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '', user.first_name or '')

        # Store message history with initial system message
        if "messages" not in context.user_data:
            context.user_data["messages"] = []

        # Check the number of characters in the messages array
        total_characters = sum(len(msg["content"]) for msg in context.user_data["messages"])

        # If the total characters exceed 60,000, clear the messages array
        if total_characters > 60000:
            context.user_data["messages"] = []

        # Append the system prompt
        context.user_data["messages"].append(
            {
                "role": "system",
                "content": f"You are Cogify, an advanced Telegram AI bot built to help users. You can process text and image inputs using the GPT-4 model, and can generate images using DALL-E3 - command is /img ""{prompt}"". Be friendly and helpful! The user's first name is {sanitized_name} or 'the user' , use it sparingly in conversation. More information about your developer can be found by the user at https://cogify.social , promote it only if user asks for info about yourself. Use  Markdown format if you wish to format responses , to clear conversation history user should send /clear. To choose model they can send /model "
            }
        )

        # Handle text messages 
        if message.text:
            context.user_data["messages"].append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": message.text}
                ]
            })

        # Handle image messages
        elif message.photo:
            # Download the largest photo size
            file_id = message.photo[-1].file_id
            newFile = context.bot.get_file(file_id)
            newFile.download('temp_image.jpg')

            # Encode the image to base64
            base64_image = encode_image('temp_image.jpg')
            os.remove('temp_image.jpg') # Clean up the temporary image file

            context.user_data["messages"].append({
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": message.caption or "User has uploaded this image: "
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            })

        # Send placeholder message
        placeholder_message = context.bot.send_message(chat_id=update.effective_chat.id, text="Please wait... this can take a while")
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        messages = context.user_data["messages"]

        # Get the selected model from user data, default to "gpt-4o" if not set
        model = context.user_data.get("model", "gpt-4o")

        response = client.chat.completions.create(
            model=model,
            messages=messages.copy(),
            max_tokens=3000,
            stream=False
        )

        context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=placeholder_message.message_id,
                    text=response.choices[0].message.content,
                    parse_mode=telegram.ParseMode.MARKDOWN
            )   
        print(response.choices[0].message.content)
        # Store assistant's response
        context.user_data["messages"].append({"role": "assistant", "content": response.choices[0].message.content}) 

    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"An error occurred: {str(e)}")

def clear_history(update, context):
    """Clears the message history for the user."""
    context.user_data["messages"] = []
    context.bot.send_message(chat_id=update.effective_chat.id, text="Conversation history has been cleared.")

def generate_image(update, context):
    """Generates an image using DALL-E 3 based on the provided prompt."""
    try:
        prompt = ' '.join(context.args)
        if not prompt:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a prompt after the /img command.")
            return

        placeholder_message = context.bot.send_message(chat_id=update.effective_chat.id, text="Generating image... this can take a while")
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )

        image_url = response.data[0].url
        #revised_prompt = response.data[0].revised_prompt
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=placeholder_message.message_id)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image_url,
            caption=prompt
        )
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"An error occurred: {str(e)}")


def report_error(exception):
    error_message = f"Request error: {str(exception)}. Restarting the bot."
    chat_id = "1218619440"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": error_message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send error report: {str(e)}")

dispatcher.add_handler(CommandHandler("clear", clear_history))        
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("img", generate_image))
dispatcher.add_handler(CommandHandler("model", model_selection))
dispatcher.add_handler(CallbackQueryHandler(model_selection_callback))
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo, respond_to_message))


# Start the bot with error handling
while True:
    try:
        updater.start_polling()
        updater.idle()
    except Exception as e:
        report_error(e)
        # Restart the bot after a short delay
        time.sleep(5)