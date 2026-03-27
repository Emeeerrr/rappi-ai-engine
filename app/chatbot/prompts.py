"""
Chatbot Prompts - System prompts and templates for the conversational AI.

This module will implement:
- System prompt that establishes the assistant's role as a Rappi data analyst
- Templates for injecting metric context, data summaries, and query results
- Few-shot examples for common query patterns
- Prompt formatting utilities for different LLM providers
"""

SYSTEM_PROMPT = ""
"""Base system prompt - will be populated with role definition and metric context."""

QUERY_TEMPLATE = ""
"""Template for wrapping user queries with relevant data context."""
