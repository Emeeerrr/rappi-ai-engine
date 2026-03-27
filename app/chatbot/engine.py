"""
Chatbot Engine - Core conversational logic.

This module will implement:
- Processing user queries about Rappi operational metrics
- Routing questions to the appropriate data queries
- Generating natural language responses using the LLM client
- Integrating metric context and data summaries into conversations
- Handling follow-up questions with conversation memory
"""


def process_message(user_message: str, conversation_history: list) -> str:
    """Process a user message and return the assistant's response.

    Args:
        user_message: The user's input text.
        conversation_history: List of previous messages in the conversation.

    Returns:
        The assistant's response text.
    """
    raise NotImplementedError("Chatbot engine not yet implemented")
