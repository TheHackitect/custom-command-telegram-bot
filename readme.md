Telegram Bot README
===================

Overview
--------
This Telegram bot allows you to manage custom commands and admin users through interactions in Telegram. It uses Python with the python-telegram-bot library and SQLite for database management.

Features
--------
- User Management: Registers users upon first interaction and stores their Telegram IDs for future communication.
- Command Management: Allows admins to create, edit, and delete custom commands stored in the database.
- Admin Management: Enables adding and removing admins who have access to administrative functions.
- Dynamic Command Handling: Responds to user messages that match registered commands dynamically.
- Help Command: Provides a list of available public commands and their descriptions to users.
- Start Command: Welcomes users and includes a customizable welcome message from the database, if available.

Setup Instructions
------------------
1. Clone Repository:

git clone <repository_url>
cd <repository_name>

2. Install Dependencies:
pip install -r requirements.txt


3. Configure Bot Token:
Obtain a Telegram Bot API token from BotFather and update `config.py`:
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"


4. Configure Admin ID:
Update `config.py` with your Telegram admin ID:
ADMIN_ID = <your_admin_telegram_id>

5. Database Setup:
The bot uses SQLite by default. Ensure SQLite is installed, or update `DATABASE_URL` in `config.py` for another database engine if needed:
DATABASE_URL = "sqlite:///my_bot.db"


6. Run the Bot:
Start the bot by running `bot.py`:
python bot.py

Usage
-----
- Commands:
- /start: Initializes the bot and registers the user. Includes a customizable welcome message if configured in the database.
- /help: Lists available public commands and their descriptions.
- /addcommand: Initiates the process to add a new command (admin only).
- /editcommand: Initiates the process to edit an existing command (admin only).
- /deletecommand: Initiates the process to delete an existing command (admin only).
- /addadmin: Initiates the process to add a new admin (admin only).
- /deleteadmin: Initiates the process to delete an admin (admin only).

- Dynamic Command Handling: Non-command messages are checked against registered commands in the database. If a match is found, the bot responds accordingly.

Contributions
-------------
Contributions are welcome! Feel free to fork the repository, make changes, and submit pull 