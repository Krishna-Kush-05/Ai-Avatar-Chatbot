import re

file_path = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the helper function
helper_func = '''
async def call_hf_with_retry(client, url, headers, json_body, max_retries=2):
    import asyncio
    for attempt in range(max_retries):
        try:
            response = await client.post(url, headers=headers, json=json_body)
            if response.status_code == 200:
                return response
            else:
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                return response
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            
            class FallbackResponse:
                status_code = 500
                text = f"API call failed: {str(e)}"
                def json(self):
                    return {"choices": [{"message": {"content": "I am sorry, my language model is currently unavailable or timing out. Please try again later."}}]}
            return FallbackResponse()
            
    class FallbackResponse:
        status_code = 500
        text = "Max retries reached"
        def json(self):
            return {"choices": [{"message": {"content": "I am sorry, my language model is currently unavailable or timing out. Please try again later."}}]}
    return FallbackResponse()
'''

# Find the place to inject it (e.g. after the format_sse function)
if 'def format_sse' in content and 'async def call_hf_with_retry' not in content:
    content = content.replace('def format_sse(data: str, event: str = "message") -> str:\n    return f"event: {event}\\ndata: {data}\\n\\n"', 'def format_sse(data: str, event: str = "message") -> str:\n    return f"event: {event}\\ndata: {data}\\n\\n"' + helper_func)


# 2. Replace the 3 occurrences of client.post(HF_URL
# Occurrence 1:
# async with httpx.AsyncClient(timeout=120) as client:
#     response = await client.post(HF_URL, headers=headers, json=body)
content = content.replace(
    'response = await client.post(HF_URL, headers=headers, json=body)',
    'response = await call_hf_with_retry(client, HF_URL, headers, body, max_retries=2)'
)

# Wait! The streaming generator (occurrence 1) does:
# if response.status_code != 200:
#     yield format_sse(...)
# It will yield the text from FallbackResponse. But wait, FallbackResponse has text = "API call failed..." which is fine.

# Change the timeout from 120/60 to 45
content = content.replace('timeout=120', 'timeout=45.0')
content = content.replace('timeout=60', 'timeout=45.0')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
