import os
import re
import sqlite3
import asyncio
import signal
from flask import Flask, jsonify, request, render_template
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

# Graceful exit on Ctrl+C
def signal_handler(signal, frame):
    print("Exiting gracefully...")
    asyncio.get_event_loop().stop()

# Register the signal handler for Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect('queries.db')
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
    return conn

# Connect to the database
def get_db_connection_for_sessions():
    conn = sqlite3.connect('queries_for_sessions.db')
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

# Create the queries table if it doesn't exist
def init_db2():
    with get_db_connection_for_sessions() as db2:
        db2.execute('DROP TABLE IF EXISTS queries_for_sessions')  # Drop the table if it exists
        db2.execute('''CREATE TABLE IF NOT EXISTS queries_for_sessions (
            user_id INTEGER NOT NULL,
            session_string TEXT NOT NULL
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

def clear_queries_for_specific_user(user_id):
    with get_db_connection() as db:
        db.execute('DELETE FROM queries WHERE user_id = ?', (user_id,))
        db.commit()

def clear_queries_for_specific_user_and_botname(user_id, bot_name):
    with get_db_connection() as db:
        db.execute('DELETE FROM queries WHERE user_id = ? AND bot_username = ?', (user_id, bot_name))
        db.commit()

# Insert a new query into the database
def insert_query(user_id: int, bot_username: str, query: str, name: str):
    with get_db_connection() as db:
        db.execute('INSERT INTO queries (user_id, bot_username, query, name) VALUES (?, ?, ?, ?)',
                   (user_id, bot_username, query, name))
        db.commit()  # Save changes

# Insert a new query into the database
def insert_query_for_sessions(user_id: int, sessions: str):
    with get_db_connection_for_sessions() as db2:
        db2.execute('INSERT INTO queries_for_sessions (user_id, session_string) VALUES (?, ?)',
                   (user_id, sessions))
        db2.commit()  # Save changes

def check_whether_userid_present_or_not(userid):
    with get_db_connection_for_sessions() as db2:
        # Query to check if the user ID exists in the 'queries_for_sessions' table
        result = db2.execute('SELECT COUNT(*) FROM queries_for_sessions WHERE user_id = ?', (userid,)).fetchone()
        return result[0] > 0  # Returns True if userid exists, otherwise False

def check_whether_botname_present_or_not(bot):
    with get_db_connection() as db:
        # Query to check if the bot name exists in the 'queries' table
        result = db.execute('SELECT COUNT(*) FROM queries WHERE bot_username = ?', (bot,)).fetchone()
        return result[0] > 0  # Returns True if userid exists, otherwise False

# New route for the root URL
@app.route('/')
def index():
    return render_template('index.html')  # Render the index.html file

@app.route('/api/getAll/query', methods=['GET'])
def get_queries():
    # Get 'userid' and 'bot' parameters from the query string if provided
    userid = request.args.get('userid')
    bot_name = request.args.get('bot')

    with get_db_connection() as db:
        # Case 1: Only 'userid' is provided
        if userid and not bot_name:
            if not check_whether_userid_present_or_not(userid):
                return jsonify({'error': 'User ID not found'}), 404  # Return a JSON response with a 404 error
            if not check_whether_botname_present_or_not(bot_name):
                return jsonify({'error': 'Bot Name not found'}), 404  # Return a JSON response with a 404 error
            queries = db.execute('SELECT * FROM queries WHERE user_id = ?', (userid,)).fetchall()
        
        # Case 2: Only 'bot' is provided
        elif bot_name and not userid:
            queries = db.execute('SELECT * FROM queries WHERE bot_username = ?', (bot_name,)).fetchall()
        
        # Case 3: Both 'userid' and 'bot' are provided
        elif userid and bot_name:
            if not check_whether_userid_present_or_not(userid):
                return jsonify({'error': 'User ID not found'}), 404  # Return a JSON response with a 404 error
            if not check_whether_botname_present_or_not(bot_name):
                return jsonify({'error': 'Bot Name not found'}), 404  # Return a JSON response with a 404 error
            queries = db.execute('SELECT * FROM queries WHERE user_id = ? AND bot_username = ?', (userid, bot_name)).fetchall()
        
        # Case 4: Neither 'userid' nor 'bot' is provided
        else:
            # Fetch all queries if no userid is specified
            queries = db.execute('SELECT * FROM queries').fetchall()
        
        # Convert the query result to a list of dictionaries and return as JSON
        return jsonify({'queries': [dict(row) for row in queries]})

@app.route('/api/refreshAll/query', methods=['POST'])
def refresh_queries():
    global usernames

    # Get 'userid' and 'bot' from the JSON body
    data = request.get_json()
    userid = data.get('userid')
    bot_name = data.get('bot')

    if not check_whether_userid_present_or_not(userid):
        return jsonify({'error': 'User ID not found'}), 404  # Return a JSON response with a 404 error
    
    # Use a connection for session-specific queries
    with get_db_connection_for_sessions() as db2:
        # Case 1: Only 'userid' is provided
        if userid and not bot_name:
            clear_queries_for_specific_user(userid)
            # Fetch session_string values for the specified user_id
            session_queries = db2.execute('SELECT session_string FROM queries_for_sessions WHERE user_id = ?', (userid,)).fetchall()
            print("Generating query IDs for the following usernames:")
            for username in usernames:
                print(f"- {username}")
                for query in session_queries:
                    asyncio.run(generate_query(query['session_string'], username))

            # Fetch updated queries for the specified user_id
            with get_db_connection() as db:
                queries = db.execute('SELECT * FROM queries WHERE user_id = ?', (userid,)).fetchall()
        
        # Case 2: Only 'bot' is provided
        elif bot_name and not userid:
            clear_queries_for_specific_bot(bot_name)  # Clear bot queries before inserting new ones
            # Refresh the query for the specified bot
            queries = refresh_query_for_bot(bot_name)
        
        # Case 3: Both 'userid' and 'bot' are provided
        elif userid and bot_name:
            clear_queries_for_specific_user_and_botname(userid, bot_name)
            session_queries = db2.execute('SELECT session_string FROM queries_for_sessions WHERE user_id = ?', (userid,)).fetchall()
            print("Generating query IDs for the Bot {bot_name} of the follwoing users:")
            for query in session_queries:
                asyncio.run(generate_query(query['session_string'], bot_name))
            with get_db_connection() as db:
                queries = db.execute('SELECT * FROM queries WHERE user_id = ? AND bot_username = ?', (userid, bot_name)).fetchall()
        
        # Case 4: Neither 'userid' nor 'bot' is provided
        else:
            clear_queries()  # Clear existing queries before inserting new ones
            print("Generating new query IDs for the following usernames:")
    
            # Generate new queries for all usernames
            for username in usernames:
                print(f"- {username}")
                asyncio.run(generate_queries_for_all_sessions(username))
    
            # Fetch all refreshed queries
            with get_db_connection() as db:
                queries = db.execute('SELECT * FROM queries').fetchall()
                print("Database accessed: queries refreshed")  # Log to console

    # Convert the query results to a list of dictionaries and return as JSON
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

# Function to generate query ID for a single session string
async def generate_query(session: str, bot_username: str):
    global api_id, api_hash  # Access the global variables

    client = TelegramClient(StringSession(session), api_id, api_hash)

    try:
        await client.connect()
        me = await client.get_me()
        name = me.first_name + " " + (me.last_name if me.last_name else "")
        user_id = me.id
        insert_query_for_sessions(user_id, session)  # Insert the query into the database

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
        print()

        insert_query(user_id, bot_username, query, name)  # Insert the query into the database

        await client.disconnect()

    except FloodWaitError as e:
        print(f"Rate limit encountered. Waiting for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)  # Wait for the required time
        return await generate_query(session, bot_username)  # Retry after waiting

    except Exception as e:
        await client.disconnect()
        print(f"Error while generating query: {e}")
        exit(1)

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
    init_db2()
    print("Generating query IDs for the following usernames:")
    for username in usernames:
        print(f"- {username}")
        asyncio.run(generate_queries_for_all_sessions(username))
    
    print("head over to the site http://127.0.0.1:3000 to read the api docs")
    app.run(port=3000)
