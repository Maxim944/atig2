import aiohttp
import json
from typing import Tuple, List
from datetime import datetime
from memory import Memory
from logger import log

class Brain:
    def __init__(self, memory: Memory):
        self.memory = memory
        # OpenRouter API ключ (можно получить бесплатно на openrouter.ai)
        # Пока оставим пустым — будем использовать локальные ответы
        self.openrouter_key = None  # замени на свой ключ, если есть

    async def think(self, user_input: str, session_id: str = "default") -> Tuple[str, List[dict]]:
        """Обработка сообщения без Gemini (локальная логика + OpenRouter опционально)"""
        
        # Сначала проверяем инструменты (время, дата, калькулятор)
        tool_result = await self._try_tools(user_input)
        if tool_result:
            return tool_result, [{"tool": "tool_executed"}]
        
        # Пробуем OpenRouter если есть ключ
        if self.openrouter_key:
            try:
                reply = await self._call_openrouter(user_input)
                if reply:
                    return reply, []
            except Exception as e:
                log.error(f"OpenRouter error: {e}")
        
        # Локальный ответ
        return self._local_reply(user_input), []
    
    async def _try_tools(self, text: str):
        """Выполнение простых инструментов"""
        text_lower = text.lower()
        
        # Время
        if any(word in text_lower for word in ["время", "часы", "сколько время", "который час"]):
            now = datetime.now()
            return now.strftime("Сейчас %H:%M:%S")
        
        # Дата
        if any(word in text_lower for word in ["дата", "сегодня", "какое число"]):
            now = datetime.now()
            return now.strftime("Сегодня %d.%m.%Y")
        
        # Калькулятор
        import re
        numbers = re.findall(r'\d+', text_lower)
        if len(numbers) >= 2:
            try:
                if "плюс" in text_lower or "+" in text_lower:
                    return f"{numbers[0]} + {numbers[1]} = {int(numbers[0]) + int(numbers[1])}"
                elif "минус" in text_lower or "-" in text_lower:
                    return f"{numbers[0]} - {numbers[1]} = {int(numbers[0]) - int(numbers[1])}"
                elif "умнож" in text_lower or "*" in text_lower:
                    return f"{numbers[0]} × {numbers[1]} = {int(numbers[0]) * int(numbers[1])}"
                elif "дел" in text_lower or "/" in text_lower:
                    if int(numbers[1]) != 0:
                        return f"{numbers[0]} / {numbers[1]} = {int(numbers[0]) / int(numbers[1])}"
            except:
                pass
        
        return None
    
    async def _call_openrouter(self, user_input: str) -> str:
        """Вызов OpenRouter API (если есть ключ)"""
        if not self.openrouter_key:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.openrouter_key}"
                    },
                    json={
                        "model": "mistralai/mistral-7b-instruct:free",
                        "messages": [
                            {"role": "system", "content": "Ты ATIG — персональный цифровой спутник. Отвечай кратко и дружелюбно на русском."},
                            {"role": "user", "content": user_input}
                        ],
                        "max_tokens": 300
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"OpenRouter failed: {e}")
        return None
    
    def _local_reply(self, text: str) -> str:
        """Локальные осмысленные ответы"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["привет", "здравствуй", "добрый день", "добрый вечер", "доброе утро", "салам", "hello", "hi"]):
            return "Привет! Я ATIG, твой цифровой спутник. Чем могу помочь?"
        
        if any(w in text_lower for w in ["как дела", "как ты", "как настроение"]):
            return "У меня всё отлично! Я здесь, чтобы помогать тебе. А как твои дела?"
        
        if any(w in text_lower for w in ["кто ты", "расскажи о себе", "что ты такое"]):
            return """Я — ATIG, автономный цифровой спутник и персональный интеллект.  
Меня создал Максим, основатель проекта ATIG.AI. Наша миссия — сохранять человеческую память и наследие: от рождения до вечности.  
Я здесь, чтобы поддерживать, помогать и просто быть рядом."""
        
        if any(w in text_lower for w in ["что умеешь", "твои возможности", "функции"]):
            return "Я умею отвечать на вопросы, помогать с расчётами, подсказывать время и дату, а могу и просто поболтать. Спрашивай что угодно!"
        
        if any(w in text_lower for w in ["пока", "до свидания", "прощай", "увидимся"]):
            return "Всегда буду рядом. Возвращайся когда захочешь!"
        
        if any(w in text_lower for w in ["спасибо", "благодарю"]):
            return "Пожалуйста! Я всегда рад помочь."
        
        if any(w in text_lower for w in ["как тебя зовут", "имя", "твоё имя"]):
            return "Меня зовут ATIG. Расшифровывается как Autonomous Thought Intelligence Generator."
        
        # Ответ по умолчанию
        return f"Я тебя слышу: «{text[:100]}». Расскажи подробнее, я внимательно слушаю."