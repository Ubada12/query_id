# 🛠️ How to Set Up Your Query ID Extractor Bot 🛠️

## 1. Install required libraries 📦
Run this in your terminal:
```
pip install -r requirements.txt
```

## 2. Edit the .env file 📝
After installation, open the `.env` file in a text editor and update the following parameters:
- API ID
- API Hash
- Bot Usernames

Save the file after making changes. 💾

## 3. Create or transfer session files 📂
You have two options for handling session files:
- Create sessions: use your bot to generate session files.
- Paste existing sessions: if you already have session files, put the `sessions` folder into the same directory where your bot files are located.

Notes:
- Ensure your session files are in string format.
- Pyrogram session files are not accepted. If you have Pyrogram sessions, convert them into string format before proceeding.

## 4. Run the bot 🚀
Start the bot with:
```
python menu.py
```

---

🎉 That's it! Enjoy using your Query ID Extractor Bot! 🎉
