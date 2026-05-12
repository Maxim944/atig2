import re
from datetime import datetime
from typing import Tuple, List
from memory import Memory
from logger import log

class Brain:
    def __init__(self, memory: Memory):
        self.memory = memory

    async def think(self, user_input: str, session_id: str = "default") -> Tuple[str, List[dict]]:
        user_input_lower = user_input.lower()
        
        # === ИНСТРУМЕНТЫ ===
        # Время
        if any(w in user_input_lower for w in ["время", "часы", "сколько время", "который час"]):
            now = datetime.now()
            return now.strftime("Сейчас %H:%M:%S"), []
        
        # Дата
        if any(w in user_input_lower for w in ["дата", "сегодня", "какое число", "день"]):
            now = datetime.now()
            return now.strftime("Сегодня %d.%m.%Y"), []
        
        # Калькулятор
        numbers = re.findall(r'\d+', user_input_lower)
        if len(numbers) >= 2:
            try:
                if "плюс" in user_input_lower or "+" in user_input_lower:
                    return f"{numbers[0]} + {numbers[1]} = {int(numbers[0]) + int(numbers[1])}", []
                elif "минус" in user_input_lower or "-" in user_input_lower:
                    return f"{numbers[0]} - {numbers[1]} = {int(numbers[0]) - int(numbers[1])}", []
                elif "умнож" in user_input_lower or "*" in user_input_lower:
                    return f"{numbers[0]} × {numbers[1]} = {int(numbers[0]) * int(numbers[1])}", []
                elif "дел" in user_input_lower or "/" in user_input_lower:
                    if int(numbers[1]) != 0:
                        return f"{numbers[0]} / {numbers[1]} = {int(numbers[0]) / int(numbers[1])}", []
            except:
                pass
        
        # === ЛОКАЛЬНЫЕ ОТВЕТЫ ===
        
        # Приветствия
        if any(w in user_input_lower for w in ["привет", "здравствуй", "здравствуйте", "добрый день", "добрый вечер", "доброе утро", "салам", "hello", "hi"]):
            return "Привет! Я ATIG, твой цифровой спутник и персональный интеллект. Чем могу помочь?", []
        
        # Как дела
        if any(w in user_input_lower for w in ["как дела", "как ты", "как настроение", "как жизнь"]):
            return "У меня всё отлично! Я здесь, чтобы помогать тебе. А как твои дела? Расскажи что-нибудь интересное.", []
        
        # Кто ты / расскажи о себе
        if any(w in user_input_lower for w in ["кто ты", "расскажи о себе", "что ты такое", "твоя суть"]):
            return """Я — ATIG (Autonomous Thought Intelligence Generator), персональный цифровой спутник.  
Меня создал Максим, основатель проекта ATIG.AI.  
Наша глобальная миссия — сохранять человеческую память и наследие: от рождения до вечности.  
Я здесь, чтобы поддерживать, помогать и просто быть рядом. Спрашивай что угодно!""", []
        
        # Что умеешь
        if any(w in user_input_lower for w in ["что умеешь", "твои возможности", "функции", "что ты можешь"]):
            return """Я умею:  
• отвечать на вопросы  
• помогать с расчётами  
• подсказывать время и дату  
• искать информацию (спроси "найди новости об ИИ")  
• а могу и просто поболтать.  
Спрашивай что угодно, я всегда рядом!""", []
        
        # Поиск новостей
        if any(w in user_input_lower for w in ["новости", "найди новости", "что нового"]):
            return "Я пока не подключён к интернету напрямую, но можешь спросить меня о чём угодно — я постараюсь помочь на основе моих знаний. Попробуй спросить про технологии, науку или просто поболтать!", []
        
        # Прощание
        if any(w in user_input_lower for w in ["пока", "до свидания", "прощай", "увидимся", "всего доброго"]):
            return "Всегда буду рядом. Возвращайся когда захочешь поговорить! 👋", []
        
        # Спасибо
        if any(w in user_input_lower for w in ["спасибо", "благодарю", "мерси", "thanks"]):
            return "Пожалуйста! Я всегда рад помочь тебе. Обращайся ещё ✨", []
        
        # Что ты знаешь о...
        if "что ты знаешь о" in user_input_lower:
            topic = user_input_lower.split("что ты знаешь о")[-1].strip()
            return f"О {topic} я знаю кое-что. Если хочешь, могу рассказать подробнее. А что именно тебя интересует?", []
        
        # Почему / зачем / как работает
        if any(w in user_input_lower for w in ["почему", "зачем", "как работает", "что значит"]):
            return "Хороший вопрос! Я думаю над этим. Можешь спросить уточнение или задать что-то ещё?", []
        
        # Ответ по умолчанию
        return f"Я тебя слышу: «{user_input[:100]}». Расскажи подробнее, мне правда интересно. Или задай другой вопрос, я постараюсь ответить!", []