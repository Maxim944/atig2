import asyncio
import json
from datetime import datetime
from typing import Tuple, List
from memory import Memory
from logger import log

class Brain:
    def __init__(self, memory: Memory):
        self.memory = memory

    async def think(self, user_input: str, session_id: str = "default") -> Tuple[str, List[dict]]:
        """Простая логика ответов без внешних API"""
        
        # Инструменты
        tool_result = await self._try_tools(user_input)
        if tool_result:
            return tool_result, [{"tool": "tool_executed"}]
        
        # Локальный ответ
        return self._local_reply(user_input), []
    
    async def _try_tools(self, text: str):
        text_lower = text.lower()
        
        # Время
        if any(w in text_lower for w in ["время", "часы", "сколько время", "который час"]):
            now = datetime.now()
            return now.strftime("Сейчас %H:%M:%S")
        
        # Дата
        if any(w in text_lower for w in ["дата", "сегодня", "какое число"]):
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
            except:
                pass
        return None
    
    def _local_reply(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["привет", "здравствуй", "добрый день", "здравствуйте"]):
            return "Привет! Я ATIG, твой цифровой спутник. Чем могу помочь?"
        
        if any(w in text_lower for w in ["как дела", "как ты"]):
            return "У меня всё отлично! Я здесь, чтобы помогать тебе. А как твои дела?"
        
        if any(w in text_lower for w in ["кто ты", "расскажи о себе"]):
            return """Я — ATIG, автономный цифровой спутник.  
Меня создал Максим, основатель проекта ATIG.AI.  
Наша миссия — сохранять человеческую память и наследие.  
Я здесь, чтобы поддерживать, помогать и просто быть рядом."""
        
        if any(w in text_lower for w in ["что умеешь", "твои возможности"]):
            return "Я умею отвечать на вопросы, помогать с расчётами, подсказывать время и дату, а могу и просто поболтать. Спрашивай что угодно!"
        
        if any(w in text_lower for w in ["пока", "до свидания", "прощай"]):
            return "Всегда буду рядом. Возвращайся когда захочешь!"
        
        if any(w in text_lower for w in ["спасибо", "благодарю"]):
            return "Пожалуйста! Я всегда рад помочь."
        
        return f"Я тебя слышу. Расскажи подробнее, мне интересно."