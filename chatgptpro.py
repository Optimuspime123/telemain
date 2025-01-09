import openai
from usersettingmanager import (load_chat_model,load_custom_system_prompt,load_image_quality,change_custom_prompt)
import google.generativeai as genai
import requests
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.inference.models import AssistantMessage, UserMessage, SystemMessage
import anthropic
import os
from dotenv import load_dotenv, dotenv_values


# Load environment variables from .env file
load_dotenv()

#For Llama
llama = ChatCompletionsClient(
    endpoint= os.getenv('LLAMA_ENDPOINT'),
    credential=AzureKeyCredential(os.getenv('LLAMA_KEY')),
)

#FOR Cohere
cohere = ChatCompletionsClient(
    endpoint= os.getenv('COHERE_ENDPOINT'),
    credential=AzureKeyCredential(os.getenv('COHERE_KEY')),
)

#For Mistral AI
mistral = ChatCompletionsClient(
    endpoint= os.getenv('MISTRAL_ENDPOINT'),
    credential=AzureKeyCredential(os.getenv('MISTRAL_KEY')),
)

#For Claude 
claude = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=os.getenv('ANTHROPIC_API_KEY'),
)


# Your OpenAI API key (ensure this is set securely, preferably as an environment variable)
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))    # Gemini API key

perplexity_api = os.getenv('PERPEXILITY_API_KEY')


openai.api_key = os.getenv('OPENAI_API_KEY')

model_image = "dall-e-3"  # For image generation (DALL·E)
model_speech = "whisper-1"  # For speech-to-text (Whisper)

# Initialize a dictionary to store conversation history for each user
user_sessionsopenai = {}
user_sessionadvopenai = {}
user_sessionsgemini = {}
user_sessions_perplexity = {}
user_sessions_claude = {}
user_sessions_llama = {}

def get_or_create_sessionopenai(user_id):
    # Retrieve the user's session, or create a new one if it doesn't exist
    if user_id not in user_sessionsopenai:
        user_sessionsopenai[user_id] = []
    return user_sessionsopenai[user_id]

def get_or_create_sessionadvanceopenai(user_id):
    # Retrieve the user's session, or create a new one if it doesn't exist
    if user_id not in user_sessionadvopenai:
        user_sessionadvopenai[user_id] = []
    return user_sessionadvopenai[user_id]

def get_or_create_sessiongemini(user_id):
    # Retrieve the user's session, or create a new one if it doesn't exist
    if user_id not in user_sessionsgemini:
        user_sessionsgemini[user_id] = []
    return user_sessionsgemini[user_id]

def get_or_create_session_perplexity(user_id):
    # Retrieve the user's session, or create a new one if it doesn't exist
    if user_id not in user_sessions_perplexity:
        user_sessions_perplexity[user_id] = []
    return user_sessions_perplexity[user_id]

def get_or_create_session_claude(user_id):
    # Retrieve the user's session, or create a new one if it doesn't exist
    if user_id not in user_sessions_claude:
        user_sessions_claude[user_id] = []
    return user_sessions_claude[user_id]

def get_or_create_session_llama(user_id):
    # Retrieve the user's session, or create a new one if it doesn't exist
    if user_id not in user_sessions_llama:
        user_sessions_llama[user_id] = []
    return user_sessions_llama[user_id]

def test_openai_key(user_id, prompt, img_url=None):

    model_chat = load_chat_model(user_id)

    customprompt = load_custom_system_prompt(user_id)
    if not customprompt:
        customprompt =  "You are Cogify, an advanced Telegram AI bot built to help users. You can process text (and image inputs using the GPT-4o model), and can generate images using DALL-E3 - command is /img {prompt}. Be friendly and helpful!  to clear conversation history user should send /clear. To choose settings and change AI Model used they can send /settings . To get results from the internet they can use /web {query}"
    chatgptmodels = {"o1-preview","o1-mini","chatgpt-4o-latest","gpt-4","gpt-4o","gpt-4o-mini","gpt-4-turbo","gpt-3.5-turbo"}
    geminimodels = {"gemini-2.0-flash-exp","gemini-2.0-flash-thinking-exp-1219","gemini-exp-1206","gemini-1.5-pro","gemini-1.5-flash"}
    claudemodels = {"claude-3-5-sonnet-20241022","claude-3-5-haiku-20241022","claude-3-haiku-20240307","claude-3-opus-20240229","claude-3-sonnet-20240229","claude-2.1","claude-2.0"}
    perplexitymodels = {"llama-3.1-sonar-small-128k-online","llama-3.1-sonar-large-128k-online","llama-3.1-sonar-huge-128k-online"}

    if model_chat in chatgptmodels:

        if model_chat == "o1-preview" or model_chat == "o1-mini": #Doesnt Supports Custom Prompt
            # Get or create the user's conversation history
            openai_conversation_history = get_or_create_sessionadvanceopenai(user_id)
            # Add user message to conversation history
            openai_conversation_history.append({"role": "user", "content": prompt})

            try:
                # Use the chat completions method with the model "o1-preview-2024-09-12"
                response = openai.ChatCompletion.create(
                    model=model_chat,  # You can use other models like "gpt-4"
                    messages=openai_conversation_history  # Use the entire conversation history
                )

                # Get the model's response
                assistant_reply = response.choices[0].message.get("content")

                # Add assistant's reply to the conversation history
                openai_conversation_history.append({"role": "assistant", "content": assistant_reply})

                return assistant_reply
            except openai.OpenAIError as e:  # Catch any OpenAI error
                return f"An error occurred: {e}"
            except Exception as e:
                return f"Unexpected error: {e}"
            
        else: #Supports Custom Prompt
            # Get or create the user's conversation history
            openai_conversation_history = get_or_create_sessionopenai(user_id)
            if not openai_conversation_history:
                openai_conversation_history.append({"role": "system", "content": customprompt})
            
            # Add user message to conversation history
            if img_url:
                openai_conversation_history.append({
                    "role": "user",
                     "content": prompt,
                    "type": "image_url",
                    "image_url": img_url
                     
                })
            else:
                openai_conversation_history.append({"role": "user", "type": "text", "content": prompt})

            try:
                # Use the chat completions method with the model "o1-preview-2024-09-12"
                response = openai.ChatCompletion.create(
                    model=model_chat,  # You can use other models like "gpt-4"
                    messages=openai_conversation_history  # Use the entire conversation history
                )

                # Get the model's response
                assistant_reply = response.choices[0].message.get("content")

                # Add assistant's reply to the conversation history
                openai_conversation_history.append({"role": "assistant", "content": assistant_reply})

                return assistant_reply
            except openai.OpenAIError as e:  # Catch any OpenAI error
                return f"An error occurred: {e}"
            except Exception as e:
                return f"Unexpected error: {e}"

        
    elif model_chat in geminimodels:
        # Get or create the user's conversation history
        gemini_conversation_history = get_or_create_sessiongemini(user_id) #history.append({"role": "user", "parts": prompt})
        gemini_conversation_history.append({"role": "user", "parts": prompt}) #({"role": "model", "parts": response.text})

        try: 
            genai.GenerativeModel(model_chat)
            response = model_chat.generate_content(gemini_conversation_history)

            if model_chat == "gemini-2.0-flash-thinking-exp-1219":
                reply = response.candidates[0].content.parts[1].text
            else:
                reply = response.text

            gemini_conversation_history.append({"role": "model", "parts": reply})
            return reply
        
        except Exception as e:
            return f"Unexpected error: {e}"
        
    elif model_chat == "llama":
        lamahistory = get_or_create_session_llama(user_id)
        if not lamahistory:
            lamahistory.append({"role": "system", "content": customprompt})

        lamahistory.append({"role": "user", "content": prompt})

        try:
            response = llama.complete(
                messages=lamahistory
            )
            lamareply = response.choices[0].message.content
            lamahistory.append({"role": "assistant", "content": lamareply})
            return lamareply
        except HttpResponseError as ex:
            if ex.status_code == 400:
                response = ex.response.json()
                if isinstance(response, dict) and "error" in response:
                    return f"Your request triggered an {response['error']['code']} error:\n\t {response['error']['message']}"
                else:
                    raise
            raise

    elif model_chat == "cohere":
        lamahistory = get_or_create_session_llama(user_id)
        if not lamahistory:
            lamahistory.append({"role": "system", "content": customprompt})

        lamahistory.append({"role": "user", "content": prompt})
        try:
            response = cohere.complete(
                messages=lamahistory
            )
            coherereply =  response.choices[0].message.content 
            lamahistory.append({"role": "assistant", "content": coherereply})
            return coherereply
            
        except HttpResponseError as ex:
            if ex.status_code == 400:
                response = ex.response.json()
                if isinstance(response, dict) and "error" in response:
                    return f"Your request triggered an {response['error']['code']} error:\n\t {response['error']['message']}"
                else:
                    raise
            raise

    elif model_chat == "mistral":
        lamahistory = get_or_create_session_llama(user_id)
        if not lamahistory:
            lamahistory.append({"role": "system", "content": customprompt})

        lamahistory.append({"role": "user", "content": prompt})
        try:
            response = mistral.complete(
                messages=lamahistory
            )
            mistralreply =  response.choices[0].message.content
            lamahistory.append({"role": "assistant", "content": mistralreply})
            return mistralreply
        except HttpResponseError as ex:
            if ex.status_code == 400:
                response = ex.response.json()
                if isinstance(response, dict) and "error" in response:
                    return f"Your request triggered an {response['error']['code']} error:\n\t {response['error']['message']}"
                else:
                    raise
            raise

    elif model_chat in perplexitymodels:
        
        perplexityhistory = get_or_create_session_perplexity(user_id)
        # Check if the conversation history is empty, then add the system message
        if not perplexityhistory:
            perplexityhistory.append({"role": "system","content": customprompt })

        perplexityhistory.append({"role": "user","content": prompt})

        payload = {"model": model_chat,"messages": perplexityhistory}
        headers = {
            "Authorization": f"Bearer {perplexity_api}",
            "Content-Type": "application/json"
        }
        url = "https://api.perplexity.ai/chat/completions"
        response = requests.request("POST", url, json=payload, headers=headers)
        perp_reply = response.json()["choices"][0]["message"]["content"]

        # Add assistant's reply to the conversation history
        perplexityhistory.append({"role": "assistant", "content": perp_reply})
        return perp_reply
        
    elif model_chat in claudemodels:
        try:

            if model_chat == "claude-3-5-sonnet-20241022" or model_chat =="claude-3-5-haiku-20241022":
                max_token = 8000
            else:
                max_token = 4000

            claudehistory = get_or_create_session_claude(user_id)
            claudehistory.append({
                "role": "user",
                "content": prompt
            })
            # Create the messages for Claude model
            if model_chat in claudemodels:
                # Create a message with the Claude API
                message = claude.messages.create(
                    model=model_chat,
                    max_tokens=max_token,
                    system=customprompt,  # Pass system as a top-level parameter
                    messages=claudehistory
                )

                # Extract the content of the assistant's reply
                claudereply = message.content[0].text  # Assuming 'message['text']' will give the assistant's reply
                claudehistory.append({"role": "assistant", "content": claudereply})
                return claudereply
            else:
                return f"Model '{model_chat}' is not supported."
        except Exception as e:
            # Handle any errors during the API call
            return f"Error occurred with model {model_chat}: {e}"
            
    else:
        return "No such Models"
    



def getfluximage(prompt):
    """Generates an image using flux based on the provided prompt."""
    try:
        url = f"https://api.airforce/imagine2?model=Flux&prompt={prompt}"
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise RuntimeError(f"Failed to generate image with flux: {str(e)}")

    
# Function for generating an image using DALL·E, using conversation history
def generate_image(user_id, prompt):
    # Get or create the user's conversation history
    conversation_history = get_or_create_sessionopenai(user_id)
    quality = load_image_quality(user_id)
    if quality == "flux":
        try:
            url = f"https://api.airforce/imagine2?model=Flux&prompt={prompt}"
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise RuntimeError(f"Failed to generate image with flux: {str(e)}")
    elif quality == "dalle3satndard":
        selected_quality = "standard"
    elif quality == "dalle3hd":
        selected_quality = "hd"

    # Add user message to conversation history for the image request (this can be part of the prompt)
    conversation_history.append({"role": "user", "content": prompt})

    # Combine recent conversation context with the prompt to generate an image
    conversation_context = " ".join([message["content"] for message in conversation_history[-3:]])  # Last 3 exchanges

    # Add some context to the image prompt from the conversation history
    full_prompt = f"Based on the conversation: '{conversation_context}', please create an image: {prompt}"

    try:
        response = openai.Image.create(
            model=model_image,  # You can specify the model here if needed
            prompt=full_prompt,
            n=1,
            size="1024x1024",
            quality = selected_quality
        )
        return response['data'][0]['url']  # Image URL
    except openai.OpenAIError as e:
        return f"An error occurred while generating image: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"
    

# Clear session for a specific user
def clear_session(user_id):

    change_custom_prompt(user_id,"")
    
    if user_id in user_sessionsopenai:
        # Reset the user's conversation history
        user_sessionsopenai[user_id] = []
        return f"Session cleared for user {user_id}."
    elif user_id in user_sessionsgemini:
        # Reset the user's conversation history
        user_sessionsgemini[user_id] = []
        return f"Session cleared for user {user_id}." 
    elif user_id in user_sessionadvopenai:
        # Reset the user's conversation history
        user_sessionsgemini[user_id] = []
        return f"Session cleared for user {user_id}."
    elif user_id in user_sessions_claude:
        # Reset the user's conversation history
        user_sessions_claude[user_id] = []
        return f"Session cleared for user {user_id}."  
    elif user_id in user_sessions_llama:
        # Reset the user's conversation history
        user_sessions_llama[user_id] = []
        return f"Session cleared for user {user_id}." 
    elif user_id in user_sessions_perplexity:
        # Reset the user's conversation history
        user_sessions_perplexity[user_id] = []
        return f"Session cleared for user {user_id}."
    else:
        return f"No session found for user {user_id}."
