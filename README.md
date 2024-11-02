🛠️ How to Set Up Your Query ID Extractor Bot 🛠️

1) Install Required Libraries 📦
   First, ensure you have all the necessary libraries by running the following command in your terminal:
   
   `pip install -r requirements.txt`

3) Edit the .env File 📝
   After installation, open the .env file in a text editor.
   
   Ensure you update the following parameters:
   API ID
   API Hash
   Bot Usernames
   
   Once you've made the changes, save the file. 💾
   
5) Create or Transfer Session Files 📂
   You have two options for handling session files:
   Create Sessions: Use your bot to generate session files.
   Paste Existing Sessions: If you already have session files, simply paste the "sessions" folder into the same directory where your bot files are located.
   ⚠️ Note: Ensure that your session files are in string format.
   ❗ Important: Pyrogram session files are not accepted. If you have Pyrogram sessions, please convert them into string format before proceeding.

6) Run the Bot 🚀
   Once everything is set up, execute the following command to start the bot:
   
   `python menu.py`
   
🎉 That's it! Enjoy using your Query ID Extractor Bot! 🎉
