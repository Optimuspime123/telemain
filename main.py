from user_data_manager import (add_user,removePremium ,update_credits,update_hasreferred,delete_user,get_database,get_format_database, check_user, update_subscription_topremium,add_credits,  add_group, edit_group, add_member_to_group, remove_member_from_group, check_group_members, is_user_admin)
from chatgptpro import (test_openai_key,generate_image,clear_session)
from concurrent.futures import ThreadPoolExecutor
import telebot
import os
from io import BytesIO
import time
import threading
from collections import defaultdict
from threading import Thread,Event
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from telebot.apihelper import ApiTelegramException
from usersettingmanager import(load_chat_model,load_custom_system_prompt,load_image_quality,change_chat_model,change_custom_prompt,change_image_quality)
from dotenv import load_dotenv, dotenv_values
import base64

# Load environment variables from .env file
load_dotenv()


catmaxfuryuserid = 6975177248
USER_DATA_FILE = 'user_data.json'

# Global variables

user_states = {}  # To keep track of user navigation
user_locks = defaultdict(threading.Lock)  # Dictionary to track user locks
pending_messages = []  # List to store multiple messages
user_ids = []  # This should be populated based on your audience logic


# Initialize the bot with your token
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") #Test
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
# Create a ThreadPoolExecutor with a limit on the number of concurrent threads
executor = ThreadPoolExecutor(max_workers=40)  # Adjust the number of workers as needed
lock = threading.Lock()

def parse_command(text):
    """Parse the command from the message text, supporting both / and . prefixes."""
    if text.startswith('/') or text.startswith('.'):
        command_parts = text.split()
        command_with_mention = command_parts[0]

        if '@coolcatpoolbot' in command_with_mention:
            command = command_with_mention.split('@')[0][1:]
            return command
        
        command = text.split()[0][1:]  # Remove the leading / or .
        return command.lower()

    return None


def custom(message):
    user_id = message.from_user.id
    # Check if the message starts with /custom and slice off that part
    if message.text.startswith('/custom'):
        custom_text = message.text[len('/custom '):]  # Slice off "/custom " (with space)
        change_custom_prompt(user_id,custom_text)
        bot.send_message(message.chat.id, f"Your custom prompt is: {custom_text}")
    else:
        bot.send_message(message.chat.id, "Please use the correct format: /custom {Your Prompt Here}")


pending_message = None
user_ids = []


def register_message(message):
    # Create a button to register
    markup = types.InlineKeyboardMarkup()
    register_button = types.InlineKeyboardButton("Register", url=f"https://t.me/{bot.get_me().username}?start")
    markup.add(register_button)

    busy_message = bot.reply_to(message, 
         "You are not registered. Please register yourself in private chat first.\n Auto Deleting this message in (15sec)",
          reply_markup=markup)

    # Store the message info and set a timer to delete it after 10 seconds
    busy_message_info = (busy_message.chat.id, busy_message.message_id)
    threading.Timer(15, lambda: bot.delete_message(busy_message_info[0], busy_message_info[1]) if busy_message_info else None).start()


# Command handler for /start

# Command handler for /start
def handle_start(message):
    referrer_id = message.text.split()[1][4:] if len(message.text.split()) > 1 and message.text.startswith('/start ref_') else None
    user_id = message.from_user.id
    first_name = message.from_user.full_name
    username = message.from_user.username
    chat_id = message.chat.id
    dev1 = '<a href="https://t.me/catmaxfury">CatMaxFury</a>'
    dev2 = '<a href="https://t.me/Shubhamsharmaui">Shubham Sharma</a>'
    user_data = check_user(user_id)
    if message.chat.type in ['group', 'supergroup']:
        if not user_data:
            register_message(message)
            return
    
    if user_data:
        # If user exists, display their current data
        subscription = user_data.get('subscription')
        credits = user_data.get('credits')
        refer_line = ''
        if subscription != "Premium":
         if referrer_id is not None:
            if user_data.get('used_referrence'):
               refer_line = "You have already redeemed using referal code\n\n"
            else:
               update_referrer = check_user(referrer_id)
               if update_referrer:
                  if update_referrer.get('subscription') != "Premium":
                    add_credits(referrer_id,30)
                    add_credits(user_id,30)
                    update_hasreferred(user_id,referrer_id)
                    
        if subscription == "Gold":
           credits_line = f"<b>💰 Credits</b> --> <code>{credits}</code>\n"
        elif subscription == "Admin" or user_id == 1384248924:
            subscription = "Owner"
            credits_line = ''
        else:
            credits_line = ''
            
        response = (
        f"{refer_line}"
        f"🎉Welcome back <a href=\"tg://user?id={user_id}\"><b>{first_name}</b></a>! 🤖to the Cogify Bot!\n\n"
        f"<b>Subscription</b>:  <b>(🌟 {subscription})</b>\n\n"
        f"{credits_line}"
        "<b>📜 To view all available commands and their usage, type:</b> /help\n\n"
        f"<b>📩 For any issues, inquiries or purchases, contact:</b> {dev1}\n\n"
        f"<b>👨‍💻 Developers: </b>{dev1} & {dev2}\n"
        "<b>💖 Thank you for using this bot!</b>"
        )
        response += "\n(You are already registered.)"
    else:
        credits_line = ''
        # If user does not exist, register them and display the registration message
        if referrer_id is not None:      
            credits = 30,  # New user receives 10 credits
            # Credit the referrer only if referrer_id is valid
            checkreferenceid = check_user(referrer_id)
            if checkreferenceid:
                if checkreferenceid.get('subscription') != "Premium":
                    add_credits(referrer_id,30) # Referrer receives 30 credits
                    credits_line = "You joined using a referral link! You've earned 10 credits.Refer your code and earn more!!"
                    has_referred = True
                    credits = 30   
                    subscription = "Gold"  
                    credits_line = f"<b>💰 Credits</b> --> <code>{credits}</code>\n"
            else:
                has_referred = False
                credits = 0  
                subscription = "FreeUser"  
                bot.reply_to(message, "You joined but the referrer ID is invalid.")               
        else:
            has_referred = False
            subscription = "Premium"
            credits = 0
        add_user(user_id, first_name, credits, subscription, username,referrer_id,has_referred)
        response = (
        f"Hello <a href=\"tg://user?id={user_id}\"><b>{first_name}</b></a>! 🤖\n\n"
        f"<b>Subscription</b>:  <b>(🌟 {subscription})</b>\n"
        f"{credits_line}"
        "<b>🎉 Welcome to the Cogify Bot!</b> 🚀\n\n"
        "<i>Thank you for starting the bot.🙏</i>\n\n"
        "<b>📜 To view all available commands and their usage, type:</b> /help\n\n"
        f"<b>📩 For any issues, inquiries or purchases, contact:</b> {dev1}\n\n"
        f"<b>👨‍💻 Developers: </b>{dev1} & {dev2}\n"
        "<b>💖 Thank you for using this bot!</b>\n"
        )
        response += "You are now registered."
     
    if message.chat.type in ['group', 'supergroup']:
          response += "\n\n Deleting this message in 10 Seconds to prevent group spam.. You can see the message in prvt."   
    busy_message = bot.reply_to(message,response,parse_mode = "HTML")
    if message.chat.type in ['group', 'supergroup']:
          busy_message_info = (busy_message.chat.id, busy_message.message_id)
          threading.Timer(10, lambda: bot.delete_message(busy_message_info[0], busy_message_info[1]) if busy_message_info else None).start()
    
       
def typing_animation(chat_id, message_id, stop_event):
    """Function to simulate typing animation."""
    messages = [
        "Typing",
        "Typing.",
        "Typing..",
        "Typing...",
        "Typing...."
    ]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set():
                break
            try:
                bot.edit_message_text(msg, chat_id, message_id)
                time.sleep(0.5)  # Adjust the speed of the animation
            except Exception as e:
                break

# Function to download an image from a URL
def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return BytesIO(response.content)  # Return image as a BytesIO object
    except requests.RequestException as e:
        return None
    
# Function for typing animation
def gen_animation(chat_id, message_id, stop_event):
    """Function to simulate typing animation."""
    messages = [
        "Generating image",
        "Generating image.",
        "Generating image..",
        "Generating image...",
        "Generating image...."
    ]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set():
                break
            try:
                bot.edit_message_text(msg, chat_id, message_id)
                time.sleep(0.5)  # Adjust the speed of the animation
            except Exception as e:
                break

# Command handler for /img
def img(message):
    user_id = message.from_user.id
    user_data = check_user(user_id)
    subscription = user_data.get('subscription')

    # Ensure that the user is valid and that the command is being used in a valid context
    if message.chat.type in ['group', 'supergroup']:
        if not user_data:
            # Register the user if necessary
            register_message(message)
            return
    if subscription == "FreeUser":
        bot.reply_to(message, "You need to buy premium to use this command. Please purchase a premium subscription.")
        return
    
    # Initialize a lock for the user (prevent concurrent processing)
    user_lock = user_locks.setdefault(user_id, threading.Lock())

    try:
        # Try to acquire the lock (non-blocking)
        if not user_lock.acquire(blocking=False):
            # Notify the user that their previous command is still processing
            busy_message = bot.reply_to(message, "Your previous command is processing. Please wait.")
            threading.Timer(5, lambda: bot.delete_message(busy_message.chat.id, busy_message.message_id)).start()
            return
        
        # Extract the prompt for the image from the user's message
        prompt = message.text[len("/img "):].strip()  # Remove '/image ' from the start of the message

        # If no prompt is provided, inform the user
        if not prompt:
            bot.reply_to(message, "Please provide a prompt for the image. Example: /img A beautiful sunset")
            return
        
        # Notify the user that the image generation is in progress
        waiting_message = bot.send_message(message.chat.id, "Generating image...")
        gen_model = load_image_quality(user_id)
        # Start the typing animation in the background
        stop_event = threading.Event()
        animation_thread = threading.Thread(target=gen_animation, args=(message.chat.id, waiting_message.message_id, stop_event))
        animation_thread.start()
        # Generate the image using the prompt
        image_url = generate_image(user_id,prompt)

        # bot.send_photo(message.chat.id,photo=image_url,caption=prompt)

        # Stop the animation once the image is ready
        stop_event.set()
        

        # If there is an error in the image generation
        if "error" in image_url:
            bot.send_message(message.chat.id, f"Error: {image_url}")
        else:
                # Download the image from the URL
            image_data = download_image(image_url)
            if image_data:

                # Send the image back to the user
                bot.send_photo(message.chat.id, image_data)
            else:
                bot.send_message(message.chat.id, f"Failed to download the image. Here is the URL: {image_url}")

        # Delete the waiting message
        bot.delete_message(message.chat.id, waiting_message.message_id)

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")
    finally:
        user_lock.release()  # Ensure the lock is released after processing


# Function to encode an image to base64
def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


#Command Handler for /gpt4
@bot.message_handler(func=lambda message: parse_command(message.text) == 'gpt4')
def gpt4(message):
    
    user_id = message.from_user.id
    user_data = check_user(user_id)

    if message.chat.type in ['group', 'supergroup']:
        if not user_data:
            register_message(message)
            return

    user_lock = user_locks[user_id]
    
    try:
        if not user_lock.acquire(blocking=False):
            # Start a timer to delete the busy message after 5 seconds
            busy_message = bot.reply_to(message, "Your previous command is processing. Please wait.")
            threading.Timer(5, lambda: bot.delete_message(busy_message.chat.id, busy_message.message_id)).start()
            return

        full_text = message.text
        #print(message)
        rest_message = ""
        # Handle reply message (when someone tags another person's message)
        if message.reply_to_message:
            if message.reply_to_message.text:
                # If the reply contains text, extract and process it
                replied_message = message.reply_to_message.text
                rest_message = f"{replied_message}\n{full_text[len('/gpt4 '):].strip()}"

            elif message.reply_to_message.document:
                # If the reply is a document, handle the file content
                file_id = message.reply_to_message.document.file_id
                file_info = bot.get_file(file_id)
                file_path = file_info.file_path
                file = bot.download_file(file_path)

                # Assuming the file is a text file, decode it
                file_content = file.decode('utf-8')
                rest_message = f"{file_content}\n{full_text[len('/gpt4 '):].strip()}"
        img_url = None
        if message.photo:
            #Handle the case when user directly sends photo
            file_id = message.photo[0].file_id
            newFile = bot.get_file(file_id)
            downloaded_file = bot.download_file(newFile.file_path)
            with open("temp_image.jpg", 'wb') as new_file:
                        new_file.write(downloaded_file)            
            base64_image = encode_image('temp_image.jpg')
            img_url = f"data:image/jpeg;base64,{base64_image}"
            os.remove('temp_image.jpg')

        user_message = full_text
        if img_url and img_url.strip():
            prompt = f"User has added an image to the conversation:{message.caption if message.caption else ''}"
        else:
            prompt = user_message
      
        typing_message = bot.send_message(message.chat.id, "Typing...")

        stop_event = Event()  # Create an event to control the typing animation
        animation_thread = Thread(target=typing_animation, args=(message.chat.id, typing_message.message_id, stop_event))
        animation_thread.start()
        response = test_openai_key(user_id,prompt,img_url)  # Send the prompt to GPT-4
        stop_event.set()  # Signal the animation to stop
        animation_thread.join()  # Wait for the thread to finish

        # Send the response as a normal text message or a file
        MAX_MESSAGE_LENGTH = 4096
        if len(response) > MAX_MESSAGE_LENGTH:
            with open('response.txt', 'w', encoding="utf-8") as file:
                file.write(response)
            
            with open('response.txt', 'rb') as file:
                bot.send_document(message.chat.id, file, caption="📄 The response is too lengthy for a message, so here it is as a file!")
                bot.delete_message(message.chat.id, typing_message.message_id)
                
            os.remove('response.txt')  # Delete the file after sending
        else:
            # Send the response as a normal text message
            bot.edit_message_text(response, message.chat.id, typing_message.message_id)

    except Exception as e:
        stop_event.set()  # Signal the animation to stop
        animation_thread.join()  # Wait for the thread to finish
        bot.edit_message_text( f"An error occurred: {e}",message.chat.id,typing_message.message_id,parse_mode='HTML')
    finally:
        user_lock.release()  # Ensure the lock is released after processing

# Command handler for /clear
def clear(message):
    user_id = message.from_user.id
    user_data = check_user(user_id)
    if message.chat.type in ['group', 'supergroup']:
        if not user_data:
            register_message(message)
            return
    response = clear_session(user_id)
    bot.send_message(user_id,response)


@bot.message_handler(func=lambda message: parse_command(message.text) == 'img')
def start(message):
    executor.submit(img, message)

@bot.message_handler(func=lambda message: parse_command(message.text) == 'clear')
def start(message):
    executor.submit(clear, message)

@bot.message_handler(func=lambda message: parse_command(message.text) == 'custom')
def start(message):
    executor.submit(custom, message)


     
@bot.message_handler(func=lambda message: parse_command(message.text) == 'start')
def start(message):
    executor.submit(handle_start, message)
    
@bot.message_handler(func=lambda message: parse_command(message.text) == 'help')
def start(message):     
    send_welcome(message.chat.id)

@bot.message_handler(func=lambda message: parse_command(message.text) == 'setting')
def start(message):     
    send_welcome(message.chat.id)


@bot.message_handler(func=lambda message: parse_command(message.text) == 'settings')
def start(message):     
    send_welcome(message.chat.id)
    
    
# @bot.message_handler(func=lambda m: True)
# def process_message(message):
#     # Start handling messages in a separate thread
#     executor.submit(gpt4, message)

@bot.message_handler(content_types=['text','photo','document'])
def handle_all_messages(message):
     executor.submit(gpt4, message)

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id 
    message_id = call.message.message_id
    markup = call.message.reply_markup  # This is where we get the inline keyboard
    try:        
        if call.data == 'close_help':
            bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete the message

        if call.data == 'main_menu':
            display_main_menu(chat_id, message_id)
        elif call.data == 'back':
            current_state = user_states.get(chat_id, {}).get("current")
            if current_state == "tool_info":
                # If coming back from tool info, check what tool was displayed
                previous_state = user_states[chat_id]["previous"]
                if previous_state == "Select Model":
                    display_tool_info(chat_id, message_id, "Select Model",user_id)
                elif previous_state == "Generation Quality":
                    display_tool_info(chat_id, message_id, "Generation Quality",user_id)
                elif previous_state == "Custom System Prompt":
                    display_tool_info(chat_id, message_id, "Custom System Prompt",user_id)
                elif previous_state == "Open AI Models":
                    display_tool_info(chat_id, message_id, "Open AI Models",user_id)
                else:
                    display_main_menu(chat_id, message_id)
            else:
                send_welcome(chat_id, message_id)

        elif call.data == 'select_model':
            user_states[chat_id]["previous"] = "main_menu"  # Set previous state before switching to Select Model
            display_tool_info(chat_id, message_id, "Select Model",user_id)
        elif call.data == 'open_ai_models':
            user_states[chat_id]["previous"] = "Select Model"  # Update previous state before switching to Open AI Models
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'gemini_models':
            user_states[chat_id]["previous"] = "Select Model"  # Update previous state before switching to Open AI Models
            display_tool_info(chat_id, message_id, "Gemini Models",user_id)
        elif call.data == 'claude_models':
            user_states[chat_id]["previous"] = "Select Model"  # Update previous state before switching to Open AI Models
            display_tool_info(chat_id, message_id, "Claude Models",user_id)
        elif call.data == 'perplexity_models':
            user_states[chat_id]["previous"] = "Select Model"  # Update previous state before switching to Open AI Models
            display_tool_info(chat_id, message_id, "Perplexity Models",user_id)
        elif call.data == 'gen_quality':
            display_tool_info(chat_id, message_id, "Generation Quality",user_id)
        elif call.data == 'custom_prompt':
            display_tool_info(chat_id, message_id, "Custom System Prompt",user_id)

        elif call.data == 'save_o1_preview': #o1_preview 
            change_chat_model(user_id,"o1-preview")
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_o1-mini': #o1 Mini
            change_chat_model(user_id,"o1-mini")
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_chatgpt_4o_latest': #CHATGPT 4o Latest  #'save_chatgpt_4o_latest'), #chatgpt-4o-latest
            change_chat_model(user_id,"chatgpt-4o-latest") 
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_gpt_4': #GPT-4
            change_chat_model(user_id,"gpt-4")
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_gpt_4o': #GPT 4o 
            change_chat_model(user_id,"gpt-4o")
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_gpt_4o_mini': #GPT 4o Mini
            change_chat_model(user_id,"gpt-4o-mini")  
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_gpt_4_turbo': #GPT-3.5-Turbo   
            change_chat_model(user_id,"gpt-4-turbo")
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)
        elif call.data == 'save_gpt_35_turbo': #GPT-3.5-Turbo  
            change_chat_model(user_id,"gpt-3.5-turbo")
            display_tool_info(chat_id, message_id, "Open AI Models",user_id)

            
        elif call.data == 'save_gemini-2.0-flash-exp':   
            change_chat_model(user_id,"gemini-2.0-flash-exp")
            display_tool_info(chat_id, message_id, "Gemini Models",user_id)
        elif call.data =='save_gemini-2.0-flash-thinking-exp-1219':
            change_chat_model(user_id,"gemini-2.0-flash-thinking-exp-1219")
            display_tool_info(chat_id, message_id, "Gemini Models",user_id)
        elif call.data =='save_gemini-exp-1206' :
            change_chat_model(user_id,"gemini-exp-1206")
            display_tool_info(chat_id, message_id, "Gemini Models",user_id)
        elif call.data =='save_gemini-1.5-pro': #gemini-1.5-pro
            change_chat_model(user_id,"gemini-1.5-pro")
            display_tool_info(chat_id, message_id, "Gemini Models",user_id)
        elif call.data =='save_gemini-1.5-flash':
            change_chat_model(user_id,"gemini-1.5-flash")
            display_tool_info(chat_id, message_id, "Gemini Models",user_id) 


        elif call.data =='save_claude-3-5-sonnet-20241022':
            change_chat_model(user_id,"claude-3-5-sonnet-20241022")
            display_tool_info(chat_id, message_id, "Claude Models",user_id) 
        elif call.data =='save_claude-3-5-haiku-20241022':
            change_chat_model(user_id,"claude-3-5-haiku-20241022")
            display_tool_info(chat_id, message_id, "Claude Models",user_id) 
        elif call.data =='save_claude-3-haiku-20240307':
            change_chat_model(user_id,"claude-3-haiku-20240307")
            display_tool_info(chat_id, message_id, "Claude Models",user_id) 
        elif call.data =='save_claude-3-opus-20240229':
            change_chat_model(user_id,"claude-3-opus-20240229")
            display_tool_info(chat_id, message_id, "Claude Models",user_id)
        elif call.data =='save_claude-3-sonnet-20240229':
            change_chat_model(user_id,"claude-3-sonnet-20240229")
            display_tool_info(chat_id, message_id, "Claude Models",user_id) 
        elif call.data =='save_claude-2.1':
            change_chat_model(user_id,"claude-2.1")
            display_tool_info(chat_id, message_id, "Claude Models",user_id) 
        elif call.data =='save_claude-2.0':
            change_chat_model(user_id,"claude-2.0")
            display_tool_info(chat_id, message_id, "Claude Models",user_id) 


        elif call.data =='save_llama':
            change_chat_model(user_id,"llama")
            display_tool_info(chat_id, message_id, "Select Model",user_id) 
        elif call.data =='save_mistral':
            change_chat_model(user_id,"mistral")
            display_tool_info(chat_id, message_id, "Select Model",user_id) 
        elif call.data =='save_cohere':
            change_chat_model(user_id,"cohere")
            display_tool_info(chat_id, message_id, "Select Model",user_id)

        elif call.data =='save_llama-3.1-sonar-small-128k-online':
            change_chat_model(user_id,"llama-3.1-sonar-small-128k-online")
            display_tool_info(chat_id, message_id, "Perplexity Models",user_id)
        elif call.data =='save_llama-3.1-sonar-large-128k-online':
            change_chat_model(user_id,"llama-3.1-sonar-large-128k-online")
            display_tool_info(chat_id, message_id, "Perplexity Models",user_id)
        elif call.data =='save_llama-3.1-sonar-huge-128k-online':
            change_chat_model(user_id,"llama-3.1-sonar-huge-128k-online")
            display_tool_info(chat_id, message_id, "Perplexity Models",user_id)

        elif call.data == "save_dall-e-3standard":
            change_image_quality(user_id,"dalle3satndard")
            display_tool_info(chat_id, message_id, "Generation Quality",user_id)
        elif call.data == "save_dall-e-3hd":
            change_image_quality(user_id,"dalle3hd")
            display_tool_info(chat_id, message_id, "Generation Quality",user_id)


    except ApiTelegramException as e:
        if e.result_json['error_code'] == 400 and 'message is not modified' in e.result_json.get('description', ''):
            # Log the error or simply ignore it as the message content has not been modified
            return
        else:
            # If it's a different API error, log it or handle it
            return

# Function to send the welcome message and main menu
def send_welcome(chat_id, message_id=None):
    welcome_text = (
        "🌟 <b>Welcome to the Cogify Bot!</b> 🌟\n\n"
        "═════════════════\n"
        "✨ <b>Explore the features using navigation buttons below:</b>  \n\n"
        "🔧 <b>Some Features:</b>  \n\n"
        "• 💳 <i>Free Access to ALL AI Models</i>\n"
        "• 🔒 <i>Free Unlimited Image generation</i>\n\n"
        "🌐 Web Version: <code><a>cogify.social</a></code>\n\n"
        "💡 <i>Tip:</i> Use /help to show this message again.  \n\n"
        "═════════════════\n"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚙️ Settings", callback_data='main_menu'),
               InlineKeyboardButton("❌ Close", callback_data='close_help'))
    if message_id:
        bot.edit_message_text(welcome_text, chat_id=chat_id, message_id=message_id, reply_markup=markup,parse_mode="HTML")
    else:
        bot.send_message(chat_id, welcome_text, reply_markup=markup,parse_mode="HTML")

# Function to display the main menu
def display_main_menu(chat_id, message_id):

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🧠 Select Model", callback_data='select_model'))
    markup.add(InlineKeyboardButton("🖼️ Generation Quality", callback_data='gen_quality'))
    markup.add(InlineKeyboardButton("🔧  Custom System Prompt", callback_data='custom_prompt'))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data='back'),
               InlineKeyboardButton("❌ Close", callback_data='close_help'))  # Added Back button below

    bot.edit_message_text("🌟 Welcome to the Bot! 🌟\nUse the buttons below to navigate.\n\n🔧 Main Menu:\nChoose an option:", chat_id=chat_id, message_id=message_id, reply_markup=markup)
    user_states[chat_id] = {"current": "main_menu", "previous": None}  # Set current state

# Function to display tool information with a back button
def display_tool_info(chat_id, message_id, tool_name,user_id):
    chat_model = load_chat_model(user_id)
    genquality = load_image_quality(user_id)
    markup = InlineKeyboardMarkup()

    # Dynamically set the previous state based on the current screen
    if tool_name == "Select Model":
        markup.add(InlineKeyboardButton("🤖 Open AI   ⭐4.9", callback_data='open_ai_models'))
        markup.add(InlineKeyboardButton("🌟 Gemini   ⭐4.8", callback_data='gemini_models'))
        markup.add(InlineKeyboardButton("🧠 Claude   ⭐4.7", callback_data="claude_models"))
        markup.add(InlineKeyboardButton("🦙 Llama 3.3 70B   ⭐4.4", callback_data='save_llama'))
        markup.add(InlineKeyboardButton("🌀 Mistral-Large-2411   ⭐4.2", callback_data="save_mistral"))
        markup.add(InlineKeyboardButton("🤔 Perplexity   ⭐4.1", callback_data='perplexity_models'))
        markup.add(InlineKeyboardButton("🎯 Cohere-Command R+   ⭐4.1", callback_data='save_cohere'))

        response_text = f"🔍 Click On the Model You want to choose.!\n\nCurrent Model: {chat_model}"
        previous_state = "main_menu"  # Coming from the main menu

    elif tool_name == "Open AI Models":
                                                                                  
        markup.add(InlineKeyboardButton("o1-preview", callback_data='save_o1_preview'), #o1-preview
                   InlineKeyboardButton("o1 Mini", callback_data='save_o1-mini'))  #o1-mini
        
        markup.add(InlineKeyboardButton("CHATGPT 4o Latest", callback_data='save_chatgpt_4o_latest'), #chatgpt-4o-latest
                   InlineKeyboardButton("GPT 4", callback_data='save_gpt_4')) #gpt-4 
        
        markup.add(InlineKeyboardButton("GPT 4o", callback_data='save_gpt_4o'), #gpt-4o
                   InlineKeyboardButton("GPT-4o Mini", callback_data='save_gpt_4o_mini')) #gpt-4o-mini
        
        markup.add(InlineKeyboardButton("GPT 4 Turbo", callback_data='save_gpt_4_turbo'), #gpt-4-turbo
                   InlineKeyboardButton("GPT-3.5-Turbo", callback_data='save_gpt_35_turbo')) #gpt-3.5-turbo

        response_text = f"🔍 Choose The Open AI Model To Use!\n\nCurrent Model: {chat_model}"
        previous_state = "Select Model"  # Coming from "Select Model"

    elif tool_name == "Gemini Models":
        markup.add(InlineKeyboardButton("✨ Gemini-2.0-Flash (exp)", callback_data='save_gemini-2.0-flash-exp'))  #gemini-2.0-flash-exp
        markup.add(InlineKeyboardButton("💡 Gemini-2.0-Flash-Thinking", callback_data='save_gemini-2.0-flash-thinking-exp-1219')) #gemini-2.0-flash-thinking-exp-1219
        markup.add(InlineKeyboardButton("⚡ Gemini-Exp-1206", callback_data='save_gemini-exp-1206')) #gemini-exp-1206
        markup.add(InlineKeyboardButton("✨ Gemini-1.5-Pro", callback_data='save_gemini-1.5-pro'))  #gemini-1.5-pro
        markup.add(InlineKeyboardButton("⚡ Gemini-1.5-Flash", callback_data='save_gemini-1.5-flash'))  #gemini-1.5-flash

        response_text = f"🔍 Choose The Gemini AI Model To Use!\n\nCurrent Model: {chat_model}"
        previous_state = "Select Model"  # Coming from "Select Model"

    elif tool_name == "Claude Models":
        markup.add(InlineKeyboardButton("Claude 3.5 Sonnet", callback_data='save_claude-3-5-sonnet-20241022'))  #claude-3-5-sonnet-20241022
        markup.add(InlineKeyboardButton("Claude 3.5 Haiku", callback_data='save_claude-3-5-haiku-20241022')) #claude-3-5-haiku-20241022
        markup.add(InlineKeyboardButton("Claude 3 Haiku", callback_data='save_claude-3-haiku-20240307'))  #claude-3-haiku-20240307
        markup.add(InlineKeyboardButton("Claude 3 Opus", callback_data='save_claude-3-opus-20240229'))  #claude-3-opus-20240229
        markup.add(InlineKeyboardButton("Claude 3 Sonet", callback_data='save_claude-3-sonnet-20240229')) #claude-3-sonnet-20240229
        markup.add(InlineKeyboardButton("Claude 2.1", callback_data='save_claude-2.1'))  #claude-2.1
        markup.add(InlineKeyboardButton("Claude 2.0", callback_data='save_claude-2.0'))  #claude-2.0

        response_text = f"🔍 Choose The Claude AI Model To Use!\n\nCurrent Model: {chat_model}"
        previous_state = "Select Model"  # Coming from "Select Model"

    elif tool_name == "Perplexity Models":
        markup.add(InlineKeyboardButton("llama-3.1-sonar-small", callback_data='save_llama-3.1-sonar-small-128k-online'))  #llama-3.1-sonar-small-128k-online
        markup.add(InlineKeyboardButton("llama-3.1-sonar-large", callback_data='save_llama-3.1-sonar-large-128k-online')) #llama-3.1-sonar-large-128k-online
        markup.add(InlineKeyboardButton("llama-3.1-sonar-huge", callback_data='save_llama-3.1-sonar-huge-128k-online')) #llama-3.1-sonar-huge-128k-online

        response_text = f"🔍 Choose The Perplexity AI Model To Use!\n\nCurrent Model: {chat_model}"
        previous_state = "Select Model"  # Coming from "Select Model"


    elif tool_name == "Generation Quality":
        markup.add(InlineKeyboardButton("🎨 DALL-E-3 Standard", callback_data='save_dall-e-3standard'))
        markup.add(InlineKeyboardButton("🖼️ DALL-E 3 HD", callback_data='save_dall-e-3hd'))

        response_text = f"🔍 Choose The Image Generation Quality!\n\nCurrent Quality: {genquality}"
        previous_state = "main_menu"  # Coming from the main menu


    elif tool_name == "Custom System Prompt":
        # markup.add(InlineKeyboardButton("Save your custom prompt using\n\n/custom <Your Prompt Here>\n\n/custom You are a helpful assistant.", callback_data='save_custom_prompt'))
        response_text = "Save your custom prompt using\n\n /custom {Your Prompt Here} \n\n /custom You are a helpful assistant."
        previous_state = "main_menu"  # Coming from the main menu

    markup.add(InlineKeyboardButton("🔙 Back", callback_data='back'),
               InlineKeyboardButton("❌ Close", callback_data='close_help'))  # Back button for tool info

    bot.edit_message_text(response_text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
    
    # Now set the previous state correctly based on which screen you're on
    user_states[chat_id] = {"current": "tool_info", "previous": previous_state}  # Set current and previous state


    
    
def refresh_selected_model_message(chat_id, message_id, markup):
    # Retrieve the selected model from user states (or a database)
    selected_model = "Chatgpt 3.5 turbo"

    # Construct the new message text with the updated model
    updated_message = f"🔍 Click On the Model You want to choose.!\n\nCurrent Model: {selected_model}\n\n"

    # Update only the part of the message that shows the current model (keeping the buttons)
    bot.edit_message_text(
        updated_message,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=markup,  # Keep the same keyboard
        parse_mode="HTML"
    )

    
bot.infinity_polling()
