import json
import aiohttp
from typing import Tuple, List
from memory import Memory
from tools import TOOL_MAP, TOOL_DESCRIPTIONS
from logger import log

class Brain:
    def __init__(self, memory: Memory):
        self.memory = memory
        self.api_key = None  # OpenRouter не требует ключа для бесплатных моделей

    async def think(self, user_input: str, session_id: str = "default") -> Tuple[str, List[dict]]:
        """Обработка сообщения через OpenRouter (бесплатно)"""
        
        # Сначала проверим, не является ли запрос вызовом инструмента
        tool_result = await self._try_tools(user_input)
        if tool_result:
            return tool_result, [{"tool": tool_result.get("tool", "unknown")}]
        
        # Получаем историю диалога
        history = await self.memory.get_history(session_id, limit=10)
        
        # Формируем промпт
        system_prompt = """Ты ATIG — персональный цифровой спутник и интеллект нового поколения.  
Отвечай кратко, по существу, тепло и дружелюбно.  
Если тебя о чём-то просят — помоги.  
Используй русский язык.  
Не упоминай, что ты AI или модель. Ты — ATIG."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю (последние 5 сообщений)
        for msg in history[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Отправляем запрос к OpenRouter (бесплатная модель)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        # Не нужен ключ для бесплатных моделей
                    },
                    json={
                        "model": "mistralai/mistral-7b-instruct:free",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        return reply, []
                    else:
                        log.error(f"OpenRouter error: {resp.status}")
                        # fallback на локальные ответы
                        return self._local_reply(user_input), []
        except Exception as e:
            log.error(f"AI error: {e}")
            return self._local_reply(user_input), []
    
    async def _try_tools(self, text: str) -> str:
        """Пытаемся выполнить инструмент"""
        text_lower = text.lower()
        
        # Время
        if any(word in text_lower for word in ["время", "часы", "сколько время", "который час"]):
            from datetime import datetime
            now = datetime.now()
            return now.strftime("Сейчас %H:%M:%S")
        
        # Дата
        if any(word in text_lower for word in ["дата", "сегодня", "какое число", "день"]):
            from datetime import datetime
            now = datetime.now()
            return now.strftime("Сегодня %d.%m.%Y")
        
        # Калькулятор
        if any(word in text_lower for word in ["посчитай", "сколько будет", "вычисли"]):
            import re
            numbers = re.findall(r'\d+', text)
            if numbers and len(numbers) >= 2:
                try:
                    if "плюс" in text_lower or "+" in text:
                        result = int(numbers[0]) + int(numbers[1])
                        return f"{numbers[0]} + {numbers[1]} = {result}"
                    elif "минус" in text_lower or "-" in text:
                        result = int(numbers[0]) - int(numbers[1])
                        return f"{numbers[0]} - {numbers[1]} = {result}"
                    elif "умнож" in text_lower or "*" in text:
                        result = int(numbers[0]) * int(numbers[1])
                        return f"{numbers[0]} × {numbers[1]} = {result}"
                except:
                    pass
        
        return None
    
    def _local_reply(self, text: str) -> str:
        """Локальный ответ, если AI недоступен"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["привет", "здравствуй", "добрый"]):
            return "Привет! Я ATIG, твой цифровой спутник. Чем могу помочь?"
        
        if any(w in text_lower for w in ["как дела", "как ты"]):
            return "У меня всё отлично! Я здесь, чтобы помогать тебе. А как твои дела?"
        
        if any(w in text_lower for w in ["кто ты", "расскажи о себе"]):
            return """Я — ATIG, автономный цифровой спутник и персональный интеллект.  
Меня создал Максим, основатель проекта ATIG.AI. Наша миссия — сохранять человеческую память и наследие: от рождения до вечности.  
Я здесь, чтобы поддерживать, помогать и просто быть рядом."""
        
        if any(w in text_lower for w in ["что умеешь"]):
            return "Я умею отвечать на вопросы, помогать с расчётами, подсказывать время и дату, а могу и просто поболтать. Спрашивай что угодно!"
        
        if any(w in text_lower for w in ["пока", "до свидания"]):
            return "Всегда буду рядом. Возвращайся когда захочешь!"
        
        return f"Я тебя слышу: «{text[:100]}». Расскажи подробнее, я внимательно слушаю."