# openai-telegram-bot

 Telegram chatbot that uses OpenAI's GPT API to generate responses
 Chatbot also translates voice messages to text and uses them as input
 when user says
- /new, start a new conversation
- /role, set the role of the user
- /stats, show usage statistics
- /suggestions <number>, show <number> suggestions in keyboard
- /help writes the help message


VOICE_MODEL = "whisper-1"
TEXT_MODEL  = "gpt-3.5-turbo"


# Screenshot
![Capture](https://user-images.githubusercontent.com/86234226/222886181-b24ba6ac-9486-45d0-94c4-08b804dfb215.PNG)


# Installation
To use this script, you will need to have Python 3.7 or later installed. You can download Python from the official website.

You will also need to install the following Python packages:
```
openai
aiogram
pydub
```

also you will need to install ffmpeg to convert voice messages to format that Whisper can transcribe to text

# Usage
1. Clone this repository to your local machine.
2. Create an account on the [OpenAI website](https://beta.openai.com/) and obtain an API key.
3. Create a api_key.py file in the same directory as the script, and add your OpenAI API key to it.
```
key = "YOUR_API_KEY"
```
4. Create a new bot on Telegram and obtain the bot_token.
5. Run the script using the following command:
```
python openaitelegram.py
```
6. Start a conversation with the bot on Telegram 
7. use /new command to start a new conversation.


# To Do
- [x] Add basic statistics
- [x] Add suggestions keyboard
- [x] Add incoming voice messages support
- [ ] Add feedback pool
- [ ] Add outgoing voice messages support
- [ ] Add web-site summary and Q&A
- [ ] Add document Q&A using langchain

# Note
You need to run this script on a server so that it can run 24/7, otherwise it will run only when you run the script on your local machine.
Works on my Raspberry Pi 2 Model B

# Additional Resources
[Telethon documentation](https://docs.telethon.dev/en/stable/index.html#)

[OpenAI API documentation](https://beta.openai.com/docs/guides/completion/introduction)

[Creating a Telegram bot](https://core.telegram.org/bots)

# License
This script is licensed under the MIT license. Feel free to use and modify it for your own projects

# Contribution
Feel free to contribute to this project by creating a pull request. Any contributions are welcome and appreciated.
