"""
Conversational Memory - Manages conversation state and context window.

This module will implement:
- Conversation history storage (list of message dicts)
- Context window management to stay within token limits
- Summary generation for long conversations
- Session persistence (optional, for Streamlit session state)
"""


class ConversationMemory:
    """Manages conversation history and context for the chatbot.

    Will handle message storage, context window trimming,
    and conversation summarization for long sessions.
    """

    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self.messages: list[dict] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        raise NotImplementedError

    def get_messages(self) -> list[dict]:
        """Return the conversation history formatted for the LLM."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages = []
