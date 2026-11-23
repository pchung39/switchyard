from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import random
import time

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    max_tokens: int | None = None

@app.post("/v1/chat/completions")
async def create_chat_completion(chat: ChatRequest):
    await asyncio.sleep(random.uniform(0.2, 2.0))
    created = int(time.time())
    answer = "Fake answer."
    prompt_tokens = sum(len(m.content.split()) for m in chat.messages)
    completion_tokens = len(answer.split())
    if chat.max_tokens is not None:
        completion_tokens = min(completion_tokens, chat.max_tokens)

    return {
        "id": f"fake-{created}",
        "object": "chat.completion",
        "created": 1732300000,
        "model": chat.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
