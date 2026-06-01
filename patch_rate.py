import re

file_path = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add slowapi imports
imports_to_add = '''from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
'''

if 'from slowapi import Limiter' not in content:
    content = imports_to_add + content

# 2. Add limiter init after app = FastAPI()
limiter_init = '''app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
'''
content = content.replace('app = FastAPI()', limiter_init)

# 3. Add decorator and Request param to /query endpoint
# Find async def query(
# Note: we also have async def query_eval(, but the user specified /query endpoint.
# But it's safer to just replace it directly.
query_pattern = r'(@app\.post\(\"/query\"\)\nasync def query\()(\s*payload:\s*Dict\[str,\s*Any\]\s*=\s*Body\(\.\.\.\),)'
query_repl = r'@app.post("/query")\n@limiter.limit("10/minute")\nasync def query(\n    request: Request,\n    payload: Dict[str, Any] = Body(...),'

content = re.sub(query_pattern, query_repl, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
