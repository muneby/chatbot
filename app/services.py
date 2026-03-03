import openai
import os
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from .models import get_order_status, search_product, get_bot_instruction

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Check order status via phone number",
            "parameters": {
                "type": "object",
                "properties": {"phone_number": {"type": "string"}},
                "required": ["phone_number"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "Search for products, prices, and stock",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }
    }
]


def get_ai_response(user_message: str, bot_id: int, db: Session, history: list = None):
    if history is None:
        history = []

    system_instruction = get_bot_instruction(bot_id, db)

    # بناء قائمة الرسائل: النظام + التاريخ + الرسالة الجديدة
    messages = [{"role": "system", "content": system_instruction}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        function_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        result = None
        if function_name == "get_order_status":
            result = get_order_status(args.get("phone_number"))
        elif function_name == "search_product":
            result = search_product(args.get("query"), bot_id, db)

        messages.append(response_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": result or "لا توجد نتائج"
        })

        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return final.choices[0].message.content

    return response_message.content
