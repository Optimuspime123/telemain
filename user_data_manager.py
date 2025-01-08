import json
from datetime import datetime, timedelta
import telebot

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

def add_user(user_id, name, credits=None, subscription=None, username=None,referrer_id = None,used=None):
    """Add a new user to the database."""
    database = load_database()
    users = database["privateuser"]
    if str(user_id) in users:
        return f"User with ID {user_id} already exists."
    
    used = referrer_id is not None

    users[str(user_id)] = {
        "userid": user_id,
        "name": name,
        "credits": credits,
        "subscription": subscription,
        "username": username,
        "referrer": referrer_id,
        "used_referrence": used,
        "chat_model": "gpt-4o",
        "image_quality": "dalle3hd",
        "custom_prompt": ""
        }
    save_database(database)
    return f"User {name} with ID {user_id} has been added."

def check_user(user_id):
    """Check if a user exists in the database."""
    database = load_database()
    users = database["privateuser"] 
    return users.get(str(user_id), None)

def removePremium(user_id,bot_token = None):
    database = load_database()
    users = database["privateuser"]
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    
    end_date_str = users[str(user_id)].get('end_date')
    users[str(user_id)]["active"] = False 
    credits = users[str(user_id)].get('credits')
    if credits < 1:
        subscription = "FreeUser"
        users[str(user_id)]["subscription"] = "FreeUser" 
    elif credits > 0:   
        subscription = "Gold"
        users[str(user_id)]["subscription"] = "Gold" 
     
    save_database(database)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S.%f')  # Convert to datetime
    # Construct the message
    result = (
    f"🔔 <b>Attention User {user_id}!</b> 🔔\n\n"
    f"Your <b>Premium Subscription</b> has expired as of <b>{end_date}</b> and reverted to {subscription}. We hope you enjoyed the benefits! 🌟\n\n"
    f"Don't miss out on all the great features! Consider renewing your subscription to continue enjoying premium content and perks. 💳✨\n\n"
    f"If you have any questions or need assistance, feel free to reach out!\n\n"
    f"Thank you for being a valued member of our community! 🙌"
    )
    telebot.TeleBot(bot_token).send_message(user_id, result, parse_mode="HTML")
    return f"User {user_id}'s premium has expired."
    

def delete_user(user_id):
    
    """Update the subscription of a user."""
    database = load_database()
    users = database["privateuser"]
    
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist." 
    del users[str(user_id)]
    save_database(database)
    
    return f"User {user_id} has been removed from the database"

def update_hasreferred(user_id,referrer_id):
    """Update the subscription of a user."""
    database = load_database()
    users = database["privateuser"]
    
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
  
    users[str(user_id)]["used_referrence"] = True
    users[str(user_id)]['referrer_id'] = referrer_id
    save_database(database)
    return f"User {user_id}'s reference has been set to true"


def update_subscription_topremium(user_id,daysactive = None,bot_token = None):
    """Update the subscription of a user."""
    database = load_database()
    users = database["privateuser"]
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    if users[str(user_id)].get('subscription') == 'Premium':
        return f'User {user_id} is already a premium'
    # users[str(user_id)]["subscription"] = "Premium"
    first_name = users[str(user_id)].get('name')
    if daysactive: 
         daysactive = int(daysactive)
         start_date = datetime.now()
         end_date = start_date + timedelta(days=daysactive)
         users[str(user_id)]['subscription'] = "Premium" 
         
         # Check if 'active' exists and update it accordingly
         if str(user_id) in users and 'active' in users[str(user_id)]:
         # Update to the new value if it exists
            users[str(user_id)]['active'] = True
         else:
        # If it doesn't exist, set it to the new value
            users.setdefault(str(user_id), {})  # Ensure the user entry exists
            users[str(user_id)]['active'] = True  
            
         if str(user_id) in users and 'end_date' in users[str(user_id)]:
         # Update to the new value if it exists
            users[str(user_id)]['end_date'] = end_date.isoformat()
         else:
         # If it doesn't exist, set it to the new value
            users.setdefault(str(user_id), {})  # Ensure the user entry exists
            users[str(user_id)]['end_date'] = end_date.isoformat() 
            
         if str(user_id) in users and 'start_date' in users[str(user_id)]:
         # Update to the new value if it exists
            users[str(user_id)]['start_date'] = start_date.isoformat()
         else:
         # If it doesn't exist, set it to the new value
            users.setdefault(str(user_id), {})  # Ensure the user entry exists
            users[str(user_id)]['start_date'] = start_date.isoformat() 

         save_database(database)
         
         result =  (f"<b>🎉 Congratulations <a href=\"tg://user?id={user_id}\"><b>{first_name} </b></a> 🎉</b>\n\n"
            f"Your subscription has been upgraded to <b>Premium</b>! 🌟\n\n"
            f"📅 <b>Start Date:</b> {start_date.strftime('%d %B %Y')}\n"
            f"📅 <b>End Date:</b>   {end_date.strftime('%d %B %Y')}\n\n"
            f"Enjoy your premium features! 🚀")
         telebot.TeleBot(bot_token).send_message(user_id, result, parse_mode="HTML")
         return (f"<b>{user_id}</b>\n"
            f"Subscription has been upgraded to <b>Premium</b>! 🌟\n\n"
            f"📅 <b>Start Date:</b> {start_date.strftime('%d, %B %Y')}\n"
            f"📅 <b>End Date:</b> {end_date.strftime('%d, %B %Y')}\n\n"
            f"Enjoy your premium features! 🚀")

def update_credits(user_id, credits):
    """Update the credits of a user and adjust their subscription status accordingly."""
    database = load_database()
    users = database.get("privateuser", {})
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    
    # Determine subscription status
    if credits < 1:
        subscription = "FreeUser"
    else:
        subscription = "Gold"
    
    # Update user information
    users[str(user_id)]["subscription"] = subscription
    users[str(user_id)]["credits"] = credits
    users[str(user_id)]["active"] = False
    
    # Save updated database
    save_database(database)
    
    return (f"Userid {user_id} credits have been updated to {credits}. "
            f"User is now a {subscription}.")
    
def update_referrer(user_id, credits):
    """Update the credits of a user and adjust their subscription status accordingly."""
    database = load_database()
    users = database.get("privateuser", {})
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    # Update user information
    users[str(user_id)]["has_referred"] = True
    # Save updated database
    save_database(database)
    
def add_credits(user_id, addcredits):
    """Update the credits of a user and adjust their subscription status accordingly."""
    database = load_database()
    credits = fetch_credits(user_id)
    users = database.get("privateuser", {})
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    credits = addcredits + credits
    # Update user information
    users[str(user_id)]["subscription"] = "Gold"
    users[str(user_id)]["credits"] = credits
    # Save updated database
    save_database(database)
    return (user_id,credits)


def fetch_credits(user_id):
    """Fetch the credits of a user."""
    database = load_database()
    users = database["privateuser"]
    
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    credits = users[str(user_id)].get("credits", 0)
    return credits

def add_group(chat_id, group_name, role):
    """Add a new group to the database."""
    database = load_database()
    groups = database["groups"]
    
    if str(chat_id) in groups:
        return f"Group with chat ID {chat_id} already exists."
    
    groups[str(chat_id)] = {
        "chat_id": chat_id,
        "group_name": group_name,
        "role": role,
        "members": {}
    }
    save_database(database)
    return f"Group {group_name} with chat ID {chat_id} has been added."

def edit_group(chat_id, group_name=None, role=None):
    """Edit an existing group in the database."""
    database = load_database()
    groups = database["groups"]
    
    if str(chat_id) not in groups:
        return f"Group with chat ID {chat_id} does not exist."
    
    if group_name:
        groups[str(chat_id)]["group_name"] = group_name
    if role:
        groups[str(chat_id)]["role"] = role
    
    save_database(database)
    return f"Group with chat ID {chat_id} has been updated."

def add_member_to_group(chat_id, user_id, role):
    """Add a member to a group."""
    database = load_database()
    groups = database["groups"]
    users = database["privateuser"]
    
    if str(chat_id) not in groups:
        return f"Group with chat ID {chat_id} does not exist."
    
    if str(user_id) not in users:
        return f"User with ID {user_id} does not exist."
    
    groups[str(chat_id)]["members"][str(user_id)] = role
    save_database(database)
    return f"User {user_id} has been added to group {chat_id} with role {role}."

def remove_member_from_group(chat_id, user_id):
    """Remove a member from a group."""
    database = load_database()
    groups = database["groups"]
    
    if str(chat_id) not in groups:
        return f"Group with chat ID {chat_id} does not exist."
    
    if str(user_id) not in groups[str(chat_id)]["members"]:
        return f"User with ID {user_id} is not a member of group {chat_id}."
    
    del groups[str(chat_id)]["members"][str(user_id)]
    save_database(database)
    return f"User {user_id} has been removed from group {chat_id}."

def check_group_members(chat_id):
    """Check the members of a group."""
    database = load_database()
    groups = database["groups"]
    
    if str(chat_id) not in groups:
        return f"Group with chat ID {chat_id} does not exist."
    
    return groups[str(chat_id)].get("members", {})

def is_user_admin(bot, chat_id, user_id):
    """Check if a user is an admin in a group."""
    try:
        administrators = bot.get_chat_administrators(chat_id)
        for admin in administrators:
            if admin.user.id == user_id:
                return True
    except Exception as e:
        print(f"Error checking admin status: {e}")
    return False

def get_database(data):
    """Get User database for sending message or getting data"""
    database = load_database()
    users_data = database["privateuser"]
           
    if data == "all":
        return [(user_info['userid']) for user_id, user_info in users_data.items()]
        # return [
        #     user_info
        #     for userid, user_info in users_data.items()
        # ]
    elif data == "Premium" or data == "premium" or data == "prem":
        return [
            user_id
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "Premium"
        ]
        
    elif data == "FreeUser" or data == "freeuser" or data == "free":
        return [
            user_id
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "FreeUser"
        ]
    elif data == "Gold" or data == "gold":   
        return [
            user_id
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "Gold"
        ]
    
    elif data == "LowCredits" or data == "low":   
        return [
        user_id
        for user_id, user_info in users_data.items()
        if user_info['subscription'] == "Gold" and user_info['credits'] < 5
    ]

 
 
def get_format_database(data):
    """Get User database for sending message or getting data"""
    database = load_database()
    users_data = database["privateuser"]
           
    if data == "all":
         return [(user_id, user_info['name']) for user_id, user_info in users_data.items()]

    elif data == "Premium" or data == "premium" or data == "prem":
        return [
            (user_id, user_info['name'])
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "Premium"
        ]
        
    elif data == "FreeUser" or data == "freeuser" or data == "free":
        return [
            (user_id, user_info['name'])
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "FreeUser"
        ]
    elif data == "Gold" or data == "gold":   
        return [
            (user_id, user_info['name'])
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "Gold"
        ]
    
    elif data == "LowCredits":   
        return [
            (user_id, user_info['name'])
            for user_id, user_info in users_data.items()
            if user_info['subscription'] == "Gold" and user_info['credits'] < 5
        ]
        
    else:
        return "No Such data found"