import asyncio
import time

import httpx

base_url = "http://localhost:8001"

payload = {
    "model": "fake-model",
    "messages": [
        {"role": "user", "content": "Hello from call_once"},
    ],
    "max_tokens": 50,
}


async def one_request(client: httpx.AsyncClient) -> dict:
    r = await client.post(
        base_url + "/v1/chat/completions",
        json=payload,
        timeout=5.0,
    )
    r.raise_for_status()
    return r.json()


async def main():
    async with httpx.AsyncClient() as client:
        start = time.perf_counter()
        tasks = [one_request(client) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

    for data in results:
        print(data["choices"][0]["message"])
        print(data["usage"])
    print(f"elapsed: {elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
