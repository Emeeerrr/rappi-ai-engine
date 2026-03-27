"""
Conversational Memory - Manages conversation history and context window.

Stores the last N exchanges (user + assistant pairs) and provides
a summary of the current conversation topic.
"""


class ConversationMemory:
    """Manages conversation history for the chatbot.

    Keeps the most recent exchanges within a configurable limit
    and provides history formatted for LLM message lists.

    Args:
        max_exchanges: Maximum number of user/assistant pairs to retain (default 10 = 20 messages).
    """

    def __init__(self, max_exchanges: int = 10):
        self.max_exchanges = max_exchanges
        self.messages: list[dict] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message and trim if over the limit.

        Args:
            role: 'user' or 'assistant'.
            content: Message text.
        """
        self.messages.append({"role": role, "content": content})
        max_msgs = self.max_exchanges * 2
        if len(self.messages) > max_msgs:
            self.messages = self.messages[-max_msgs:]

    def get_history(self) -> list[dict]:
        """Return message history formatted for the LLM (list of role/content dicts)."""
        return list(self.messages)

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages = []

    def get_summary(self) -> str:
        """Return a brief summary of the conversation so far.

        Extracts user messages to give a sense of the topics discussed.
        """
        user_msgs = [m["content"] for m in self.messages if m["role"] == "user"]
        if not user_msgs:
            return "Sin conversacion previa."
        recent = user_msgs[-3:]
        topics = "; ".join(msg[:80] for msg in recent)
        return f"Temas recientes del usuario: {topics}"
