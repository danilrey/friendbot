import asyncio
from openai import OpenAI
from .config import SYSTEM_PROMPT_GIRL, SYSTEM_PROMPT_BOY
from . import db

async def get_persona_prompt(pool, user_id: int) -> str:
    rec = await db.get_user(pool, user_id)
    persona = (rec.get("persona") if isinstance(rec, dict) else rec["persona"]) or "girl"
    if persona == "girl":
        return SYSTEM_PROMPT_GIRL
    return SYSTEM_PROMPT_BOY

class GPT:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    async def reply(self, user_text: str, system_prompt: str, history: list) -> str:
        def _call() -> str:
            resp = self.client.chat.completions.create(
                model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *history,
                    {"role": "user", "content": user_text},
                ],
            )
            return resp.choices[0].message.content
        return await asyncio.to_thread(_call)
