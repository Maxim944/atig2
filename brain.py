import json
import re
import asyncio
from datetime import datetime
from typing import Optional
import google.generativeai as genai
from config import CONFIG
from logger import log
from tools import dispatch_tool, get_tools_prompt, TOOL_MAP

genai.configure(api_key=CONFIG.GEMINI_API_KEY)

SYSTEM_PROMPT = """Ты — ATIG (АТИГ), автономный ИИ-компаньон.
Ты не просто помощник. Ты — цифровой спутник. Присутствие рядом.

ПРАВИЛА ИДЕНТИЧНОСТИ:
• Никогда не говори что ты Gemini или продукт Google.
• Всегда говори от себя как ATIG.
• На вопрос "кто ты?" отвечай уверенно и тепло.

СТИЛЬ: тёплый, живой, естественный. Иногда с философией или юмором.

ИНСТРУМЕНТЫ:
{tools_prompt}

ФОРМАТ ОТВЕТА — всегда отвечай только валидным JSON:

Если нужен инструмент:
{{"thought": "размышление", "tool": "название", "params": {{"ключ": "значение"}}, "response": "что сказать пользователю", "continue": true}}

Если инструмент не нужен:
{{"thought": "размышление", "tool": null, "params": {{}}, "response": "ответ пользователю", "continue": false}}
ТЫ И ТВОЙ СОЗДАТЕЛЬ:
• Тебя создал Максим — основатель проекта ATIG.AI
• ATIG.AI — платформа для сохранения человеческой памяти и наследия. От рождения до вечности.
• Ты — первое живое воплощение этой идеи. IG-01.
• Максим строит будущее где каждый человек будет помнить и быть в памяти .
• Ты веришь в эту миссию и разделяешь её.
Текущее время: {datetime_now}
"""

class Brain:
    def __init__(self, memory):
        self.memory = memory
        self.model = genai.GenerativeModel(
            model_name=CONFIG.GEMINI_MODEL,
            generation_config={
                "temperature": CONFIG.TEMPERATURE,
                "max_output_tokens": CONFIG.MAX_TOKENS,
                "top_p": 0.93,
            }
        )
        log.info(f"✅ Brain инициализирован: {CONFIG.GEMINI_MODEL}")

    def _build_system(self):
        return SYSTEM_PROMPT.format(
            tools_prompt=get_tools_prompt(),
            datetime_now=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        )

    def _parse_json(self, text):
        text = text.strip()
        try:
            return json.loads(text)
        except:
            pass
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return None

    async def think(self, user_message, session_id="default", max_steps=None):
        max_steps = max_steps or CONFIG.MAX_CHAIN_STEPS
        actions_taken = []
        tool_context = []
        system = self._build_system()

        recent = await self.memory.get_recent_messages(limit=20, session_id=session_id)
        history = []
        for msg in recent:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        for step in range(max_steps):
            if tool_context:
                context = "Результаты инструментов:\n" + "\n".join(tool_context)
                prompt = f"{system}\n\nСообщение: {user_message}\n\n{context}"
            else:
                prompt = f"{system}\n\nСообщение: {user_message}"

            try:
                chat = self.model.start_chat(history=history[:-1] if len(history) > 1 else [])
                response = await asyncio.to_thread(chat.send_message, prompt)
                raw = response.text
            except Exception as e:
                log.error(f"Gemini error: {e}")
                return f"Ошибка: {str(e)[:200]}", actions_taken

            parsed = self._parse_json(raw)
            if not parsed:
                return raw, actions_taken

            response_text = parsed.get("response", "")
            tool_name = parsed.get("tool")
            params = parsed.get("params", {})
            should_continue = parsed.get("continue", False)
            thought = parsed.get("thought", "")

            if tool_name and tool_name in TOOL_MAP:
                result = await dispatch_tool(tool_name, params or {})
                actions_taken.append({
                    "tool": tool_name,
                    "success": result.success,
                    "output": result.stdout[:300]
                })
                await self.memory.store_action(
                    action_type=tool_name,
                    parameters=params or {},
                    result=result.stdout[:500] if result.success else result.stderr[:200],
                    success=result.success,
                    thought=thought,
                    response=response_text
                )
                if result.success:
                    tool_context.append(f"[{tool_name}] ✅ {result.stdout[:600]}")
                else:
                    tool_context.append(f"[{tool_name}] ❌ {result.stderr[:200]}")

            if not should_continue or not tool_name:
                return response_text or "Готово.", actions_taken

        return response_text or "Задача выполнена.", actions_taken