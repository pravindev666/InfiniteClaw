"""
InfiniteClaw — LLM Engine
Agentic tool-loop orchestrator via LiteLLM.
"""
import json
import time
import traceback
from typing import List, Dict, Optional, Callable
import litellm
from core.config import get_key, get_soul, DEFAULT_MODEL, PROVIDER_KEY_MAP
from core.local_db import (
    log_usage, log_activity, update_bot_memory,
    get_current_workspace_id, save_chat_history
)


class InfiniteClawEngine:
    """The AI brain of InfiniteClaw. Routes prompts through LiteLLM with agentic tool loops."""

    MAX_TOOL_ITERATIONS = 15

    def __init__(self):
        self._setup_keys()

    def _setup_keys(self):
        """Inject API keys into environment for LiteLLM."""
        import os
        for provider, env_var in PROVIDER_KEY_MAP.items():
            key = get_key(provider)
            if key:
                os.environ[env_var] = key

    def chat(self, messages: List[Dict], model: str = None, bot_id: str = None,
             tools: list = None, tool_executor: Callable = None,
             tool_context: str = "", server_id: str = None,
             stream: bool = False) -> str:
        """
        Main chat method with agentic tool loop.
        Returns the final assistant message text.
        """
        self._setup_keys()
        model = model or DEFAULT_MODEL
        ws_id = get_current_workspace_id()

        # Build system prompt
        soul = get_soul()
        system_msg = {"role": "system", "content": soul}
        if tool_context:
            system_msg["content"] += f"\n\n## Current Context\nYou are managing: **{tool_context}**"
            if server_id:
                system_msg["content"] += f"\nTarget server ID: `{server_id}`"

        full_messages = [system_msg] + messages

        # Agentic tool loop
        for iteration in range(self.MAX_TOOL_ITERATIONS):
            start_time = time.time()

            try:
                kwargs = {
                    "model": model,
                    "messages": full_messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = litellm.completion(**kwargs)

            except Exception as e:
                error_msg = f"LLM Error: {str(e)}"
                if ws_id:
                    log_activity(ws_id, "llm_error", error_msg)
                return error_msg

            elapsed_ms = int((time.time() - start_time) * 1000)
            choice = response.choices[0]
            message = choice.message

            # Track usage
            usage = response.usage
            if usage and ws_id:
                try:
                    log_usage(
                        ws_id, bot_id or "system", model,
                        usage.prompt_tokens, usage.completion_tokens,
                        usage.total_tokens, 0.0, elapsed_ms
                    )
                except Exception:
                    pass

            # If no tool calls, return the final answer
            if not message.tool_calls:
                return message.content or ""

            # Process tool calls
            full_messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                # Execute the tool
                if tool_executor:
                    try:
                        result = tool_executor(func_name, func_args)
                        result_str = str(result) if not isinstance(result, str) else result
                    except Exception as e:
                        result_str = f"Tool error: {str(e)}\n{traceback.format_exc()}"
                else:
                    result_str = f"Tool '{func_name}' is not available."

                # Log tool execution
                if ws_id:
                    log_activity(
                        ws_id, "tool_call", f"{func_name}({json.dumps(func_args)[:200]})",
                        tool_name=func_name, server_id=server_id,
                        raw_output=result_str[:2000]
                    )

                # Append tool result
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str[:8000],
                })

        return "Max tool iterations reached. Please try a simpler request."

    def quick_ask(self, prompt: str, model: str = None) -> str:
        """Simple one-shot prompt without tools."""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )


# Global singleton
engine = InfiniteClawEngine()
