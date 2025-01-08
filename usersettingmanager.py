import stripe
import requests
import json
import stripe

DATABASE_FILE = 'userdata.json'

def load_database():
    """Load the database from the JSON file."""
    try:
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"privateuser": {}, "groups": {}}

def save_database(database):
    """Save the database to the JSON file."""
    with open(DATABASE_FILE, 'w') as f:
        json.dump(database, f, indent=4)


# Load the SK for a given user ID
def load_chat_model(user_id):
    user_data = load_database()

    # Get user data from the loaded dictionary
    user_data_for_user = user_data["privateuser"].get(str(user_id))  # Ensure user_id is a string
    
    if user_data_for_user is None:
        return None  # No data for the user
    
    # Return the stored SK if it exists, otherwise None
    return user_data_for_user.get('chat_model', None)



# Load the SK for a given user ID
def load_image_quality(user_id):
    user_data = load_database()
    
    # Get user data from the loaded dictionary
    user_data_for_user = user_data["privateuser"].get(str(user_id))  # Ensure user_id is a string
    
    if user_data_for_user is None:
        return None  # No data for the user
    
    # Return the stored SK if it exists, otherwise None
    return user_data_for_user.get('image_quality', None)


# Load the SK for a given user ID
def load_custom_system_prompt(user_id):

    user_data = load_database()
    user_data_for_user = user_data["privateuser"].get(str(user_id))  # Ensure user_id is a string
    
    if user_data_for_user is None:
        return None  # No data for the user
    
    # Return the stored SK if it exists, otherwise None
    return user_data_for_user.get('custom_prompt', None)



def change_chat_model(user_id,model):

    database = load_database()
    user_id = str(user_id)
    user_data = database["privateuser"] 
    # Get user data from the loaded dictionary
    user_data_for_user = user_data.get(user_id)
 # Save the chatmodel to the user data
    user_data_for_user['chat_model'] = model
    user_data[user_id] = user_data_for_user  # Update the user data dictionary

    # Save the updated full database back to the file
    save_database(database)  # Save the entire database, not just the user data


def change_image_quality(user_id,quality):

    database = load_database()
    user_data = database["privateuser"] 
    user_id = str(user_id)
    # Get user data from the loaded dictionary
    user_data_for_user = user_data.get(user_id)
 # Save the chatmodel to the user data
    user_data_for_user['image_quality'] = quality
    user_data[user_id] = user_data_for_user  # Update the user data dictionary

    # Save the updated full database back to the file
    save_database(database)  # Save the entire database, not just the user data


def change_custom_prompt(user_id,custom_prompt):

    database = load_database()
    user_data = database["privateuser"] 
    user_id = str(user_id)
    # Get user data from the loaded dictionary
    user_data_for_user = user_data.get(user_id)
 # Save the chatmodel to the user data
    user_data_for_user['custom_prompt'] = custom_prompt
    user_data[user_id] = user_data_for_user  # Update the user data dictionary

    # Save the updated full database back to the file
    save_database(database)  # Save the entire database, not just the user data




# gpt-4o
# chatgpt-3.5-turbo
# o1-preview-2024-09-12
# gemini
