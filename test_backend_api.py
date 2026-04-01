import requests
import json

data = {
    "prompt": "你好，请回复'测试成功'几个字。",
    "model": "deepseek",
    "temperature": 0.7,
    "max_tokens": 10
}
try:
    print("Testing Backend API http://localhost:8000/api/ai/generate ...")
    res = requests.post("http://localhost:8000/api/ai/generate", json=data)
    print("STATUS", res.status_code)
    print("DATA", res.json())
except Exception as e:
    print("Error:", e)