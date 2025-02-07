import time
from collections import defaultdict

# UserChatThread Class

# This class represents a chat thread for a user, keeps track of user activity statistics and allows the
# appending of messages to the conversation history.
#
# - system: a dictionary object representing the system role and message content.
# - history: a list of dictionaries where every dictionary represents a message sent in the conversation. The dictionary has two attributes; role and content.
# - last_message_time: a float value that represents the timestamp of the last message sent in the conversation.
# - history_trim: an integer variable to limit the length of the chat thread history.
# - completion_tokens: an integer value representing the number of completion tokens used in the conversation.
# - prompt_tokens: an integer value representing the number of prompt tokens used in the conversation.
# - total_tokens: an integer value representing the total number of tokens used in the conversation.
# - sessions: an integer value representing the number of conversation sessions.
# - messages: an integer value representing the total number of messages sent in the conversation.
# - voice_messages: an integer value representing the total number of voice messages sent in the conversation.
# - duration_seconds: a float value representing the total duration of voice messages sent in the conversation.
# - session_messages: an integer value representing the number of messages sent in the current conversation session.
# - session_voice_messages: an integer value representing the number of voice messages sent in the current conversation session.
# - session_duration_seconds: a float value representing the total duration of voice messages sent in the current conversation session.

class ModelStats():
    def __init__(self):
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.total_tokens = 0
        self.sessions = 1
        self.messages = 0
        self.errors = 0

    def str(self):
        return (f"Total messages: {self.messages}\n"
        f"Prompt tokens: {self.prompt_tokens} ({self.prompt_tokens / self.total_tokens * 100:.1f}%)\n"
        f"Completion tokens: {self.completion_tokens} ({self.completion_tokens / self.total_tokens * 100:.1f}%)\n"
        f"Total tokens used: {self.total_tokens}\n")
        
class UserChatThread():
    def __init__(self):
        print("UserChatThread init")
        self.system = {"role": "system", "content": "Use metric units"}
        self.history = [self.system]
        self.last_message_time = 0
        self.history_trim = 10
        self.suggestions = 0

        self.models = defaultdict(ModelStats)
        self.sessions = 1
        self.voice_messages = 0
        self.duration_seconds = 0
        self.session_messages = 0
        self.session_voice_messages = 0
        self.session_duration_seconds = 0

    def append(self, role:str, content:str):
        """
        Appends a message to the conversation history.
        If the length of history attribute exceeds history_trim, it removes the first element of the list.
        Also, it sets the last_message_time attribute to the current time.

        :param role: a string value representing the role of the message sender.
        :param content: a string value representing the content of the message.
        :return:
        """

        if time.time() - self.last_message_time > 60 * 10: # 10 minutes
            self.history = [self.system]

        self.history.append({"role": role, "content": content})
        self.last_message_time = time.time()
        if len(self.history) > self.history_trim:
            self.history.pop(1)

    def prune(self, current_tokens:int, max_tokens:int)->bool:
        """
        Prunes the conversation history to fit the maximum number of tokens allowed.
        :param current_tokens: an integer value representing the current number of tokens used in the conversation.
        :param max_tokens: an integer value representing the maximum number of tokens allowed in the conversation.
        """
        if len(self.history) < 2:
            return False
        self.history.pop(1)
        return True

    def reset(self):
        """
        Resets the session and statistics.
        """
        self.history = [self.system]
        self.last_message_time = 0
        self.sessions += 1
        self.session_messages = 0
        self.session_duration_seconds = 0
        self.session_voice_messages = 0

    def increase_voice_usage(self, duration_seconds:float):
        """
        Increases the voice usage statistics.
        :param duration_seconds: a float value representing the duration of the voice message in seconds.
        """
        self.duration_seconds += duration_seconds
        self.session_duration_seconds += duration_seconds
        self.voice_messages += 1
        self.session_voice_messages += 1

    def increase_message_usage(self, model:str, usage:dict):
        """
        Increases the usage statistics.
        :param usage: a dictionary object representing the usage statistics.
        """
        model_stats : ModelStats = self.models[model]
        model_stats.prompt_tokens += usage["prompt_tokens"]
        model_stats.completion_tokens += usage["completion_tokens"]
        model_stats.total_tokens += usage["total_tokens"]
        model_stats.messages += 1
        self.session_messages += 1

    def increase_error(self, model:str):
        self.models[model].errors += 1
        
