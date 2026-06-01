import re
import os

backend_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
frontend_file = r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\app.py'

# 1. Patch Backend
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports and verify function
imports_to_add = '''
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

FASTAPI_API_KEY = os.getenv("FASTAPI_API_KEY", "default_key")
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != FASTAPI_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials
'''
content = content.replace('from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Query, Form', 
                          'from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Query, Form' + imports_to_add)

# Find all @app.get, @app.post, @app.delete, @app.put EXCEPT root
def add_depends(match):
    decorator = match.group(1)
    if decorator.startswith('@app.get("/")'):
        return match.group(0) # skip root
    func_def = match.group(2)
    # inject Depends(verify_api_key)
    if '(' in func_def:
        if func_def.endswith('()'):
            return decorator + '\n' + func_def[:-1] + 'api_key: str = Depends(verify_api_key))'
        else:
            return decorator + '\n' + func_def[:-1] + ', api_key: str = Depends(verify_api_key))'
    return match.group(0)

new_content = re.sub(r'(@app\.(?:get|post|delete|put)\([^\)]+\))\s*\n(async def [a-zA-Z_0-9]+\([^\)]*\):|def [a-zA-Z_0-9]+\([^\)]*\):)', add_depends, content)

with open(backend_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Backend patched.')

# 2. Patch Frontend
with open(frontend_file, 'r', encoding='utf-8') as f:
    fcontent = f.read()

# Add FASTAPI_HEADERS
fcontent = fcontent.replace(
    'BASE_FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://127.0.0.1:8000")',
    'BASE_FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://127.0.0.1:8000")\nFASTAPI_API_KEY = os.environ.get("FASTAPI_API_KEY", "default_key")\nFASTAPI_HEADERS = {"Authorization": f"Bearer {FASTAPI_API_KEY}"}'
)

# Replace hardcoded upload route
fcontent = fcontent.replace(
    '"http://127.0.0.1:8000/upload"',
    'BASE_FASTAPI_URL + "/upload"'
)

# Add headers=FASTAPI_HEADERS to all requests to BASE_FASTAPI_URL
# Match requests calls that use BASE_FASTAPI_URL or f"{BASE_FASTAPI_URL}"
fcontent = re.sub(
    r'(requests\.(?:get|post|delete)\(\s*(?:BASE_FASTAPI_URL|f"\{BASE_FASTAPI_URL\}")[^\)]+)(timeout=\d+)',
    r'\1headers=FASTAPI_HEADERS, \2',
    fcontent
)

# Replace the one for upload specifically, which might span lines
fcontent = re.sub(
    r'(requests\.post\(\s*BASE_FASTAPI_URL \+ "/upload",\s*files=.*?,?)\s*(data=.*?,\s*)?(timeout=\d+)',
    r'\1 \2headers=FASTAPI_HEADERS, \3',
    fcontent, flags=re.DOTALL
)

with open(frontend_file, 'w', encoding='utf-8') as f:
    f.write(fcontent)
print('Frontend patched.')
