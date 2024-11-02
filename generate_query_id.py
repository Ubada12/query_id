import os
import re
import sqlite3
import asyncio
from flask import Flask, jsonify, request
from flask_cors import CORS
from urllib.parse import unquote
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.types import InputBotAppShortName
from telethon.sessions import StringSession
from telethon import functions
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)
CORS(app)  # Enable CORS

# Global variables
api_id = None
api_hash = None
usernames = []

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect('queries.db')
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
    return conn

# Create the queries table if it doesn't exist
def init_db():
    with get_db_connection() as db:
        db.execute('DROP TABLE IF EXISTS queries')  # Drop the table if it exists
        db.execute('''CREATE TABLE IF NOT EXISTS queries (
            user_id INTEGER NOT NULL,
            bot_username TEXT NOT NULL,
            query TEXT NOT NULL,
            name TEXT NOT NULL
        )''')

# Clear the queries table
def clear_queries():
    with get_db_connection() as db:
        db.execute('DELETE FROM queries')
        db.commit()

def clear_queries_for_specific(bot_name):
    with get_db_connection() as db:
        db.execute('DELETE FROM queries WHERE bot_username = ?', (bot_name,))
        db.commit()

# Insert a new query into the database
def insert_query(user_id: int, bot_username: str, query: str, name: str):
    with get_db_connection() as db:
        db.execute('INSERT INTO queries (user_id, bot_username, query, name) VALUES (?, ?, ?, ?)',
                   (user_id, bot_username, query, name))
        db.commit()  # Save changes

# New route for the root URL
@app.route('/')
def index():
    return "Welcome to the Queries API! Use /api/queries to fetch the queries."

# Route to fetch miniapp queries
@app.route('/api/queries', methods=['GET'])
def get_queries():
    global usernames  # Accessing usernames as global
    clear_queries()  # Clear existing queries before inserting new ones
    print("Generating new query IDs for the following usernames:")
    
    # Refresh the queries by generating new IDs for all usernames
    for username in usernames:
        print(f"- {username}")
        asyncio.run(generate_queries_for_all_sessions(username))
    
    # Now fetch and return the updated queries
    with get_db_connection() as db:
        queries = db.execute('SELECT * FROM queries').fetchall()
        print("Database accessed: queries refreshed")  # Log to console on each access
        return jsonify({'queries': [dict(row) for row in queries]})

def refresh_query_for_bot(bot_name):
    print(f"Refreshing query for bot: {bot_name}")
    clear_queries_for_specific(bot_name)  # Clear bot queries before inserting new ones
    print(f"Generating new query IDs for the {bot_name} bot:")
    asyncio.run(generate_queries_for_all_sessions(bot_name))
    
    # Fetch and return the updated queries
    with get_db_connection() as db:
        queries = db.execute('SELECT * FROM queries WHERE bot_username = ?', (bot_name,)).fetchall()
        print("Database accessed: queries refreshed")  # Log to console on each access
        return {'queries': [dict(row) for row in queries]}  # Return the queries in the expected format

# Route to refresh a specific query for a mini-app
@app.route('/api/refresh/query', methods=['GET'])
def refresh_query():
    bot_name = request.args.get('bot')  # Get the bot name from the query parameters
    if not bot_name:
        return jsonify({"error": "Bot name is required."}), 400  # Return error if bot name is missing

    # Call the function to refresh the query for the specified bot
    queries = refresh_query_for_bot(bot_name)
    
    return jsonify({"status": "Query refreshed successfully for bot: " + bot_name, **queries})

# Function to generate query ID for a single session string
async def generate_query(session: str, bot_username: str):
    global api_id, api_hash  # Access the global variables

    client = TelegramClient(StringSession(session), api_id, api_hash)

    try:
        await client.connect()
        me = await client.get_me()
        name = me.first_name + " " + (me.last_name if me.last_name else "")
        user_id = me.id

        # Request the web app view
        webapp_response = await client(functions.messages.RequestAppWebViewRequest(
            peer=bot_username,
            app=InputBotAppShortName(bot_id=await client.get_input_entity(bot_username), short_name="app"),
            platform="ios",
            write_allowed=True,
            start_param="6094625904"
        ))

        # Parse query data from the URL
        query = unquote(webapp_response.url.split("tgWebAppData=")[1].split("&")[0])
        print(f"Successfully Query ID generated for user {name} | Bot: {bot_username} | username: {username}")

        insert_query(user_id, bot_username, query, name)  # Insert the query into the database

        await client.disconnect()

    except FloodWaitError as e:
        print(f"Rate limit encountered. Waiting for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)  # Wait for the required time
        return await generate_query(session, bot_username)  # Retry after waiting

    except Exception as e:
        await client.disconnect()
        print(f"Error while generating query: {e}")
        return None

# Function to load session strings from the 'sessions' folder and generate queries
async def generate_queries_for_all_sessions(bot_username: str):
    session_folder = 'sessions'
    
    if not os.path.exists(session_folder):
        print(f"Error: '{session_folder}' folder not found.")
        return

    for session_file in os.listdir(session_folder):
        if session_file.endswith('.session'):
            session_path = os.path.join(session_folder, session_file)
            print(f"\nProcessing session file: {session_file}")

            with open(session_path, 'r') as file:
                session_string = file.read().strip()

            await generate_query(session_string, bot_username)

# Example usage
if __name__ == '__main__':
    load_dotenv(find_dotenv())

    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    usernames_str = os.getenv('BOT_USERNAMES')

    if api_id is None or api_hash is None:
        print("Error: API_ID and API_HASH must be set in the .env file.")
        exit(1)

    if api_id.strip() == "" or api_hash.strip() == "":
        print("Error: API_ID and API_HASH cannot be empty.")
        exit(1)

    try:
        api_id = int(api_id)
    except ValueError:
        print("Error: API_ID must be an integer.")
        exit(1)

    # Validate BOT_USERNAMES
    if usernames_str is None:
        print("Error: BOT_USERNAMES must be set in the .env file.")
        exit(1)

    usernames = [username.strip() for username in usernames_str.split(",") if username.strip()]
    
    if not usernames:
        print("Error: BOT_USERNAMES cannot be empty.")
        exit(1)
    
    init_db()  # Initialize the database once at startup
    print("Generating query IDs for the following usernames:")
    for username in usernames:
        print(f"- {username}")
        asyncio.run(generate_queries_for_all_sessions(username))
    
    print("head over to the site http://127.0.0.1:3000/api/queries to see all the queries generated")
    app.run(port=3000)
