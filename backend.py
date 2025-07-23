import os
from dotenv import load_dotenv

# Simulate retrieval-GPT placeholder
def get_response(question: str):
    response = "This is a placeholder response for: " + question
    sources = [
        type("SourceNode", (object,), {"metadata": {"title": "Sample Lecture", "educator": "Jason Foster"}})()
    ]
    return response, sources
