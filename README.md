# YusarinBot

Simple, clear, easy, reliable.  
A specially designed bot for creating private voice channels at your servers.  
Installation instructions are listed below. Please, make sure you have installed dependencies before opening issue here.

## Installation (Short)
1. `git clone https://github.com/profitrollgame/YusarinBot`
2. `cd YusarinBot`
3. `pip install -r requirements.txt`
4. `nano config.json`
5. `python yusarin.py`

## Installation (Detailed)
1. Download and install Python 3 (3.6+ should be fine)
2. Download bot's release: https://github.com/profitrollgame/YusarinBot/releases/latest
3. Unpack your archive to folder. Name it YusarinBot for example
4. Change working directory using `cd YusarinBot` or `cd FolderYouHaveCreated`
5. Run `pip install -r requirements.txt` to install dependencies
6. Create new Discord application at https://discord.com/developers/applications
7. You can rename it however you want, set needed descriptions etc
8. Go to "Bot" tab and enable application as bot
9. Copy token of your bot
10. Open file `config.json` with your favorite text editor and paste your token as value of "bot_token" key
11. Copy your own Discord ID and paste it as value of "owner" key (How to get ID: https://support.playhive.com/discord-user-id/)
12. Bot is ready! Run it using `python yusarin.py`

## Config explanation
- "owner" - Discord ID of user who will be able to execute admin commands (`$shutdown` for example) [Integer]
- "bot_name" - Name of your bot. Is not used anywhere yet [String]
- "bot_token" - Token of your Discord bot [String]
- "bot_prefix" - Default prefix for all bot commands [String]
- "bot_locale" - Default language file of bot. Name of file in `locale` folder without extension is used [String]
- "bot_activity" - The name (string) of the song bot will be listening to [String]
- "check_for_updates" - Option that defines whether bot should check for a new version available [Boolean]
- "auto_clear_trash" - Option that defines whether bot should clean all buggy inactive channels every "auto_clear_timer" seconds [Boolean]
- "auto_clear_timer" - Option that defines how often "auto_clear_trash" will do its job [Integer]

## Extra
1. Bot doesn't have any self updaters **yet**
2. You can add public version of the bot to your Discord server using this link: https://discord.com/api/oauth2/authorize?client_id=937839388853944390&permissions=318769168&scope=bot
