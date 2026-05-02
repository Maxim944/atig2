import asyncio
import json
import math
import os
import platform
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import urllib.request
import urllib.parse
from logger import log

@dataclass
class ToolResult:
    success: bool
    stdout: str
    stderr: str = ""
    return_code: int = 0

TOOL_DEFINITIONS = []
TOOL_MAP = {}

def tool(name, description, parameters):
    def decorator(func):
        TOOL_DEFINITIONS.append({"name": name, "description": description, "parameters": parameters})
        TOOL_MAP[name] = func
        return func
    return decorator

@tool("web_search", "Поиск в интернете", {"query": "str"})
async def web_search(query):
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "ATIG/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        if data.get("AbstractText"):
            results.append(f"📌 {data['AbstractText']}")
        for r in data.get("RelatedTopics", [])[:5]:
            if isinstance(r, dict) and r.get("Text"):
                results.append(f"• {r['Text'][:200]}")
        if not results:
            results = ["Результаты не найдены."]
        return ToolResult(success=True, stdout="\n".join(results))
    except Exception as e:
        return ToolResult(success=False, stdout="", stderr=str(e))

@tool("calculate", "Математические вычисления", {"expression": "str"})
async def calculate(expression):
    try:
        safe = {
            "__builtins__": {}, "abs": abs, "round": round,
            "min": min, "max": max, "pow": pow, "int": int, "float": float,
            "sqrt": math.sqrt, "log": math.log, "sin": math.sin,
            "cos": math.cos, "tan": math.tan, "pi": math.pi, "e": math.e,
            "ceil": math.ceil, "floor": math.floor,
        }
        result = eval(expression, safe)
        return ToolResult(success=True, stdout=f"{expression} = {result}")
    except Exception as e:
        return ToolResult(success=False, stdout="", stderr=str(e))

@tool("get_datetime", "Текущая дата и время", {})
async def get_datetime():
    now = datetime.utcnow()
    days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
    human = f"{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year}, {now.strftime('%H:%M')} UTC"
    return ToolResult(success=True, stdout=f"🕐 {human}")

@tool("system_info", "Информация о системе", {})
async def system_info():
    info = [
        f"💻 ОС: {platform.system()} {platform.release()}",
        f"🐍 Python: {platform.python_version()}",
        f"🖥️ Хост: {platform.node()}",
    ]
    try:
        import psutil
        mem = psutil.virtual_memory()
        info.append(f"🧠 ОЗУ: {mem.used//1024//1024}MB / {mem.total//1024//1024}MB ({mem.percent}%)")
        info.append(f"⚙️ CPU: {psutil.cpu_percent(interval=0.5)}%")
    except ImportError:
        pass
    return ToolResult(success=True, stdout="\n".join(info))

@tool("fetch_url", "Получить содержимое веб-страницы", {"url": "str"})
async def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ATIG/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        import re
        clean = re.sub(r"<[^>]+>", " ", content)
        clean = re.sub(r"\s+", " ", clean).strip()
        return ToolResult(success=True, stdout=f"🌐 {url}\n\n{clean[:3000]}")
    except Exception as e:
        return ToolResult(success=False, stdout="", stderr=str(e))

@tool("remember", "Сохранить факт в память", {"category": "str", "key": "str", "value": "str"})
async def remember(category, key, value):
    return ToolResult(success=True, stdout=f"✅ Запомнено: [{category}] {key} = {value}")

def get_tools_prompt():
    lines = []
    for t in TOOL_DEFINITIONS:
        lines.append(f'• {t["name"]}: {t["description"]}')
    return "\n".join(lines)

async def dispatch_tool(action, parameters):
    if action not in TOOL_MAP:
        return ToolResult(success=False, stdout="", stderr=f"Инструмент не найден: {action}")
    try:
        clean = {k: v for k, v in parameters.items() if v is not None}
        result = await asyncio.wait_for(TOOL_MAP[action](**clean), timeout=30)
        if isinstance(result, ToolResult):
            return result
        return ToolResult(success=True, stdout=str(result))
    except asyncio.TimeoutError:
        return ToolResult(success=False, stdout="", stderr="Тайм-аут")
    except Exception as e:
        return ToolResult(success=False, stdout="", stderr=str(e))