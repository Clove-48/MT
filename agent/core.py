"""Agent core — Anthropic SDK call + tool loop."""

import json
import streamlit as st
import os
from anthropic import Anthropic, APIError, AuthenticationError

from .tool_definitions import TOOLS
from .tool_handlers import HANDLERS
from .prompts import SYSTEM_PROMPT

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = None
        
        try:
            if hasattr(st, 'secrets'):
                if hasattr(st.secrets, 'get'):
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
                else:
                    api_key = st.secrets["ANTHROPIC_API_KEY"].strip() if "ANTHROPIC_API_KEY" in st.secrets else ""
        except Exception:
            pass
        
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        
        if not api_key:
            raise RuntimeError("请在 Streamlit Secrets 或环境变量中设置 ANTHROPIC_API_KEY")
        
        if not api_key.startswith("sk-"):
            raise RuntimeError(f"无效的 API 密钥格式：密钥应以 'sk-' 开头")
        
        _client = Anthropic(api_key=api_key)
    return _client


def run_agent_with_retry(user_message: str, chat_history: list[dict] = None,
                         model: str = "claude-sonnet-4-6", max_retries: int = 2) -> str:
    """Run agent with retry logic for authentication errors."""
    global _client
    
    for attempt in range(max_retries):
        try:
            return run_agent(user_message, chat_history, model)
        except AuthenticationError as e:
            if attempt < max_retries - 1:
                _client = None
                continue
            raise RuntimeError(f"认证失败：{str(e)}。请检查您的 API 密钥是否正确且未过期。")
        except APIError as e:
            raise RuntimeError(f"API 调用失败：{str(e)}")


def run_agent(user_message: str, chat_history: list[dict] = None,
              model: str = "claude-sonnet-4-6") -> str:
    """Run the agent with a user message and return the final response text.

    Args:
        user_message: The user's natural language input.
        chat_history: List of previous messages in Anthropic format
                      [{"role": "user"|"assistant", "content": ...}].
        model: Claude model ID.

    Returns:
        The agent's final text response (after tool loop completes).
    """
    client = _get_client()
    messages = (chat_history or []) + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect text and tool_use blocks
        text_parts = []
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # If no tool calls, agent is done — return the text
        if not tool_uses:
            return "\n".join(text_parts)

        # Add assistant message (with tool_use blocks) to history
        messages.append({
            "role": "assistant",
            "content": [b.to_dict() for b in response.content]
        })

        # Execute tools and build tool_result blocks
        tool_results = []
        for tu in tool_uses:
            handler = HANDLERS.get(tu.name)
            if handler is None:
                result = {"error": f"Unknown tool: {tu.name}"}
            else:
                try:
                    result = handler(**tu.input)
                except Exception as e:
                    result = {"error": str(e)}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

        # Add tool results to history
        messages.append({"role": "user", "content": tool_results})


def run_agent_streaming(user_message: str, chat_history: list[dict] = None,
                        model: str = "claude-sonnet-4-6"):
    """Streaming version of run_agent. Yields text chunks and tool call events.

    Yields:
        dict: {"type": "text", "content": "..."} or
              {"type": "tool_start", "name": "...", "input": {...}} or
              {"type": "tool_result", "name": "...", "result": {...}} or
              {"type": "done"}
    """
    client = _get_client()
    messages = (chat_history or []) + [{"role": "user", "content": user_message}]

    while True:
        tool_uses_this_round = []

        with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            assistant_content = []
            current_text = ""

            for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "text":
                        current_text = ""
                    elif event.content_block.type == "tool_use":
                        pass  # tool_use ID tracked in tool_uses_this_round

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        current_text += event.delta.text
                        yield {"type": "text", "content": event.delta.text}
                    elif event.delta.type == "input_json_delta":
                        pass  # accumulated below

                elif event.type == "content_block_stop":
                    pass

            # After stream ends, collect the full message
            final_message = stream.get_final_message()
            for block in final_message.content:
                assistant_content.append(block.to_dict())
                if block.type == "tool_use":
                    tool_uses_this_round.append(block)

            messages.append({"role": "assistant", "content": assistant_content})

        if not tool_uses_this_round:
            yield {"type": "done"}
            return

        # Execute tools
        tool_results = []
        for tu in tool_uses_this_round:
            yield {"type": "tool_start", "name": tu.name, "input": tu.input}
            handler = HANDLERS.get(tu.name)
            if handler is None:
                result = {"error": f"Unknown tool: {tu.name}"}
            else:
                try:
                    result = handler(**tu.input)
                except Exception as e:
                    result = {"error": str(e)}
            yield {"type": "tool_result", "name": tu.name, "result": result}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

        messages.append({"role": "user", "content": tool_results})
