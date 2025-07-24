import requests

def get_response(question: str):
    response = requests.post(
        "https://168b5f18-1a60-4338-b72f-69d17778facf-00-1melv1wth7iy8.worf.replit.dev/ask",  # 👈 your Replit backend URL
        json={"question": question}  # ✅ FIXED: use "question" not "query"
    )
    response_json = response.json()
    return response_json["response"], response_json.get("sources", [])

