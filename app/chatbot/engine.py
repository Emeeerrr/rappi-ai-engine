"""
Chatbot Engine - Core conversational logic.

Implements the two-step LLM pipeline:
1. Planning: LLM maps a natural-language question to DataQueryEngine actions.
2. Response: LLM synthesizes query results into a rich, contextual answer.
"""

import json
import logging
import re

import pandas as pd

from app.config import DEFAULT_MODEL
from app.data.loader import get_dataframes
from app.data.queries import DataQueryEngine
from app.chatbot.memory import ConversationMemory
from app.chatbot.prompts import (
    FUNCTION_SCHEMA,
    build_planning_prompt,
    build_response_messages,
)
from app.utils.llm import chat_completion

logger = logging.getLogger(__name__)

_ALLOWED_METHODS = {fn["name"] for fn in FUNCTION_SCHEMA}


def _extract_json(text: str) -> dict | None:
    """Robustly extract a JSON object from LLM output.

    Tries in order: direct parse, markdown code fence, outermost braces,
    outermost brackets.
    """
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Markdown code fence (```json ... ``` or ``` ... ```)
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Outermost { ... } with brace counting
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    # 4. Outermost [ ... ] (array fallback)
    start = text.find("[")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(text[start:i + 1])
                        if isinstance(parsed, list):
                            return {"thinking": "", "actions": parsed, "direct_response": None}
                    except json.JSONDecodeError:
                        break

    return None


def _post_process_response(response: str) -> str:
    """Clean up LLM response artifacts."""
    if not response or not response.strip():
        return "No pude generar una respuesta. Por favor intenta reformular tu pregunta."

    # Clean excessive blank lines
    response = re.sub(r"\n{4,}", "\n\n\n", response)

    return response.strip()


class ChatEngine:
    """Two-step chatbot engine that translates questions into data queries.

    Args:
        model: LLM model identifier. If None, uses DEFAULT_MODEL from config.
    """

    def __init__(self, model: str | None = None):
        df_metrics, df_orders, _ = get_dataframes()
        self.query_engine = DataQueryEngine(df_metrics, df_orders)
        self.model = model or DEFAULT_MODEL
        self.memory = ConversationMemory(max_exchanges=10)
        self._planning_prompt = build_planning_prompt(FUNCTION_SCHEMA)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_query(self, user_message: str) -> dict:
        """Process a user message through the full pipeline.

        Returns:
            {"response", "charts", "raw_data", "actions_executed", "error"}
        """
        try:
            # Step 1: Planning
            plan = self._plan(user_message)

            # Handle direct responses (greetings, meta-questions, metric definitions)
            if plan.get("direct_response"):
                response_text = _post_process_response(plan["direct_response"])
                self.memory.add_message("user", user_message)
                self.memory.add_message("assistant", response_text)
                return {
                    "response": response_text,
                    "charts": [],
                    "raw_data": [],
                    "actions_executed": [],
                    "error": None,
                }

            # Step 2: Execute actions
            actions = plan.get("actions", [])
            if not actions:
                return self._fallback_response(user_message, "No se identificaron consultas para esta pregunta.")

            results, charts, raw_data, executed = self._execute_actions(actions)

            # Step 3: Generate response
            response_text = self._generate_response(user_message, results)
            response_text = _post_process_response(response_text)

            self.memory.add_message("user", user_message)
            self.memory.add_message("assistant", response_text)

            return {
                "response": response_text,
                "charts": charts,
                "raw_data": raw_data,
                "actions_executed": executed,
                "error": None,
            }

        except Exception as e:
            logger.exception("Error processing query: %s", e)
            return {
                "response": (
                    "Ocurrio un error al procesar tu pregunta. Por favor intenta reformularla.\n\n"
                    f"**Detalle tecnico:** {e}\n\n"
                    "**Preguntas sugeridas:**\n"
                    "- Cuales son las 5 zonas con peor Perfect Orders?\n"
                    "- Cual es el promedio de Lead Penetration por pais?"
                ),
                "charts": [],
                "raw_data": [],
                "actions_executed": [],
                "error": str(e),
            }

    def get_suggested_questions(self) -> list[str]:
        """Return 6 suggested questions organized by type."""
        return [
            # Overview
            "¿Cuáles son las zonas mas problemáticas esta semana?",
            "¿Cómo esta el panorama de Perfect Orders por pais?",
            # Specific
            "Top 5 zonas con mayor Lead Penetration en CO",
            "Compara Perfect Orders entre Wealthy y Non Wealthy en MX",
            # Analysis
            "¿Qué zonas tienen alto volumen de ordenes pero bajo Perfect Orders?",
            "¿Cuáles son las zonas con mayor crecimiento en ordenes?",
        ]

    def set_model(self, model: str) -> None:
        """Change the LLM model at runtime."""
        self.model = model

    def clear_memory(self) -> None:
        """Reset conversation history."""
        self.memory.clear()

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _plan(self, user_message: str) -> dict:
        """Step 1: Ask the LLM to produce an action plan as JSON."""
        messages = [
            {"role": "system", "content": self._planning_prompt},
            *self.memory.get_history(),
            {"role": "user", "content": user_message},
        ]

        raw = chat_completion(messages, model=self.model, temperature=0.1, max_tokens=2048)
        plan = _extract_json(raw)

        if plan is not None:
            return plan

        # Retry once with explicit instruction
        logger.warning("First planning attempt did not return valid JSON. Retrying...")
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                "Tu respuesta anterior no fue un JSON valido. "
                "Responde UNICAMENTE con un JSON valido: "
                "{\"thinking\": \"...\", \"actions\": [...], \"direct_response\": null}. "
                "Sin texto adicional, sin markdown."
            ),
        })

        raw_retry = chat_completion(messages, model=self.model, temperature=0.0, max_tokens=2048)
        plan = _extract_json(raw_retry)

        if plan is not None:
            return plan

        # Final fallback: treat the original response as a direct response
        logger.warning("Retry also failed. Using raw text as direct response.")
        return {"thinking": "", "actions": [], "direct_response": raw}

    def _execute_actions(self, actions: list[dict]) -> tuple[list[dict], list[dict], list, list[str]]:
        """Step 2: Execute each planned action on the DataQueryEngine."""
        results = []
        charts = []
        raw_data = []
        executed = []

        for action in actions:
            fn_name = action.get("function", "")
            params = action.get("params", {})

            if fn_name not in _ALLOWED_METHODS:
                results.append({
                    "success": False,
                    "summary": f"Metodo '{fn_name}' no reconocido. Metodos disponibles: {', '.join(sorted(_ALLOWED_METHODS)[:5])}...",
                    "chart_data": None,
                })
                continue

            method = getattr(self.query_engine, fn_name, None)
            if method is None:
                results.append({
                    "success": False,
                    "summary": f"Metodo '{fn_name}' no encontrado.",
                    "chart_data": None,
                })
                continue

            # Clean params: remove None values so defaults apply
            clean_params = {k: v for k, v in params.items() if v is not None}

            try:
                result = method(**clean_params)
            except TypeError as e:
                logger.warning("Parameter error in %s(%s): %s", fn_name, clean_params, e)
                result = {
                    "success": False,
                    "summary": f"Error de parametros en {fn_name}: {e}. Verifica los parametros enviados.",
                    "chart_data": None,
                }
            except Exception as e:
                logger.warning("Error executing %s(%s): %s", fn_name, clean_params, e)
                result = {
                    "success": False,
                    "summary": f"Error al ejecutar {fn_name}: {e}",
                    "chart_data": None,
                }

            results.append(result)
            executed.append(fn_name)

            if result.get("chart_data"):
                charts.append(result["chart_data"])
            if result.get("success") and isinstance(result.get("data"), pd.DataFrame):
                raw_data.append(result["data"])

        return results, charts, raw_data, executed

    def _generate_response(self, user_question: str, query_results: list[dict]) -> str:
        """Step 3: Ask the LLM to synthesize results into a user-facing answer."""
        messages = build_response_messages(user_question, query_results)
        return chat_completion(messages, model=self.model, temperature=0.3, max_tokens=4096)

    def _fallback_response(self, user_message: str, reason: str) -> dict:
        """Generate a fallback when planning produces no actions."""
        self.memory.add_message("user", user_message)
        suggestions = self.get_suggested_questions()[:3]
        response = (
            f"No pude determinar que datos consultar para tu pregunta. {reason}\n\n"
            "Intenta preguntar algo como:\n"
        )
        for q in suggestions:
            response += f"- {q}\n"

        response += (
            "\n**Preguntas sugeridas:**\n"
            f"- {suggestions[0]}\n"
            f"- {suggestions[1]}\n"
        )

        self.memory.add_message("assistant", response)
        return {
            "response": response,
            "charts": [],
            "raw_data": [],
            "actions_executed": [],
            "error": None,
        }
