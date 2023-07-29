import logging

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import os
from collections import defaultdict

import openai
from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType, ParseMode, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatActions

from api_key import bot_token, engine, bot_name, DEFAULT_MODEL
from user_thread import UserChatThread, ModelStats
from text_utils import entities_extract, fetch_url, is_markdown

conversations = defaultdict(UserChatThread)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

VOICE_MODEL = "whisper-1"
GPT4_MODEL = "gpt-4"

# Telegram chatbot that uses OpenAI's GPT API to generate responses
# Chatbot also translates voice messages to text and uses them as input
# when user says
# /new, start a new conversation
# /role, set the role of the user
# /stats, show usage statistics
# /suggestions <number>, show <number> suggestions in keyboard
# /help writes the help message

@dp.message_handler(commands=['help'])
async def handle_help(message):
    logging.info("user %s requested help", message.from_user.id)
    await message.answer("This is a chatbot that uses OpenAI's API to generate responses to your messages. \n"
                         "- You can start a new conversation by typing /new. \n"
                         "- You can set bot role in the conversation by typing /role. \n"
                         "- You can also send voice messages to the bot and it will transcribe them.")


@dp.message_handler(commands=['new'])
async def start_message(message: types.Message):
    conversations[message.from_user.id].reset()
    logging.info(f"Starting new conversation for {message.from_user.id}")
    await message.reply("New conversation started. Type /help for more information.",
                        reply_markup=ReplyKeyboardRemove())


@dp.message_handler(commands=['role'])
async def set_role(message: types.Message):
    # if message has no arguments, ask for role

    if len(message.text) < 6:
        logging.info("No role specified")
        current_role = conversations[message.from_user.id].system["content"]    
        await message.reply(f"Please specify a role with /role <role>\n'{current_role}' is the current role.")
        return

    conversations[message.from_user.id].system["content"] = message.text[6:]


@dp.message_handler(commands=['stats'])
async def usage_message(message: types.Message):
    conversation = conversations[message.from_user.id]

    if len(conversation.models) == 0:
        await message.answer("No usage statistics available.")
        return

    answer = ""
    total_messages = 0
    for name, value in conversation.models.items():
        stats: ModelStats = value
        total_messages += stats.messages
        answer += f"**{name}**:\n {stats.str()}\n"
        

    await message.answer(
        f"Total messages: {total_messages} in {conversation.sessions} sessions, "
        f"{conversation.session_messages} in this session. \n"
        f"Messages per session: {conversation.session_messages / conversation.sessions:.1f} \n"

        f"Total voice messages: {conversation.voice_messages} ({conversation.duration_seconds} sec), "
        f"{conversation.session_voice_messages} ({conversation.session_duration_seconds} sec) in this session. \n"
        f"Voice messages per session: {conversation.session_voice_messages / conversation.sessions:.1f} \n"

        f"{answer}\n"
    )


@dp.message_handler(commands=['suggestions'])
async def suggestions_message(message: types.Message):
    conversation = conversations[message.from_user.id]

    if len(message.text) < 12:
        logging.info("No suggestions specified")
        await message.reply("Please specify a number of suggestions with /suggestions <number>")
        return

    conversation.suggestions = int(message.text[12:])


@dp.message_handler(content_types=ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    await message.answer("Not implemented yet")


@dp.message_handler(content_types=ContentType.VOICE)
async def handle_voice(message: types.Message):
    conversation = conversations[message.chat.id]

    temp_name = f"/tmp/{message.voice.file_unique_id}.mp3"

    await message.answer_chat_action(ChatActions.RECORD_AUDIO)
    try:
        logging.debug(f"Downloading voice file to {temp_name}")
        await message.voice.download(destination_file=temp_name)

        from pydub import AudioSegment
        song = AudioSegment.from_ogg(temp_name)

        first_10_minutes = song[:10 * 60 * 1000]  # 10 minutes PyDub handles time in milliseconds
        first_10_minutes.export(temp_name, format="mp3")

        conversation.increase_voice_usage(song.duration_seconds)

        with open(temp_name, "rb") as audio_file:
            logging.debug(f"Transcribing {temp_name}")
            prompt = conversations[message.from_user.id].history[-1]["content"]
            transcript = openai.Audio.transcribe(VOICE_MODEL, audio_file, prompt=prompt)
            text = transcript["text"]

        await message.reply(f"_> {text}_", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        message.text = text
        await default_text_handler(message)

    except Exception as e:
        logging.error(e)
        await message.answer("Error occured. Please try again later.")
    finally:
        # delete the file after if it exists
        if os.path.exists(temp_name):
            logging.debug(f"Deleting {temp_name}")
            os.remove(temp_name)


@dp.message_handler(commands=['gpt4'])
async def gpt4(message: types.Message):
    await default_text_handler(message, model=GPT4_MODEL)


@dp.message_handler(content_types=ContentType.UNKNOWN)
async def handle_unknown(message: types.Message):
    await message.answer("Unknown content type.")

@dp.message_handler(content_types=ContentType.TEXT)
async def default_text_handler(message: types.Message, model: str = DEFAULT_MODEL):
    try:
        await text_handler(message, model)
    except Exception as e:
        logging.error(e)
        await message.answer("Error occured. Please try again later.\n"+str(e))

        conversation = conversations[message.chat.id]
        conversation.increase_error(model)


async def text_handler(message: types.Message, model=DEFAULT_MODEL):
    logging.debug(message.to_python())
    conversation = conversations[message.chat.id]
    is_private = message.chat.type == types.ChatType.PRIVATE

    message_text = message.text
    mentioned = False
    if message.entities:
        ee = entities_extract(message_text, message.entities)
        # Filter the entities to keep only mentions
        mentions = ee["mention"] # entities_extract(message_text, message.entities, "mention")
        
        pref_name = "@"+bot_name
        if pref_name in mentions:
            mentioned = True
            message_text = message_text.replace(pref_name, "")

        # Filter the entities to keep only mentions
        url_entities = ee["url"]
        if url_entities:
            for url_entity in url_entities:
                try:
                    res = fetch_url(url_entity)
                    message_text = message_text.replace(url_entity, '"'+ res.text_content + '"')
                except Exception as e:
                    logging.error(e)
                    #await message.answer("Error occured. Please try again later.\n"+str(e))

 

    if message_text.startswith("https://t.me/"):
        await message.reply("Please don't send links to other chats.")
        return

    await message.answer_chat_action(ChatActions.TYPING)
    if message.reply_to_message:
        role = "assistant" if message.reply_to_message.from_user.is_bot else "user"
        conversation.append(role, message.reply_to_message.text)
        mentioned = mentioned or role == "assistant"

    if message_text:
        conversation.append("user", message_text)

    if not mentioned and not is_private:
        return

    completion = await openai.ChatCompletion.acreate(
        engine=engine,
        model=model,
        messages=conversation.history
    )

    logging.debug(completion)

    answer = completion["choices"][0]["message"]["content"]
    conversation.append("assistant", answer)
    conversation.increase_message_usage (model= model, usage= completion["usage"])

    logging.debug(f"Assistant: {answer}")

    suggestions = conversation.suggestions

    if suggestions and len(answer) > 5:
        await message.answer_chat_action(ChatActions.CHOOSE_STICKER)
        completion = openai.ChatCompletion.create(
            engine=engine,
            model=model,
            n=suggestions,
            messages=[
                {"role": "system", "content": "Generate a short followup question up to 10 tokens long"},
                {"role": "user", "content": message.text},
                {"role": "assistant", "content": answer}, ],
        )
        choices = [choice["message"]["content"] for choice in completion.choices]

        markup = ReplyKeyboardMarkup(resize_keyboard=False, one_time_keyboard=True)
        markup.row_width = 1

        # Define the suggestion buttons
        buttons = [KeyboardButton(text=choice) for choice in choices]
        markup.add(*buttons)

    else:
        markup = ReplyKeyboardRemove()

    parse_mode=ParseMode.MARKDOWN if is_markdown(answer) else None    
    await message.answer(answer, parse_mode=parse_mode, reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp)
