import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever

# Load OpenAI API key from environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Set up LlamaIndex
Settings.llm = OpenAI(model="gpt-4", temperature=0.3)
Settings.embed_model = OpenAIEmbedding()
Settings.node_parser = SentenceSplitter(chunk_size=500)

# Load and chunk the cleaned transcript
reader = SimpleDirectoryReader("chunks", recursive=True)
docs = reader.load_data()
index = VectorStoreIndex.from_documents(docs)
retriever = VectorIndexRetriever(index=index, similarity_top_k=8)
engine = RetrieverQueryEngine(retriever=retriever)

# ---------- QUOTE VALIDATION UTILS ----------
def extract_candidate_quotes(text, max_sentences=3):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return set(' '.join(sentences[i:i + max_sentences]).strip()
               for i in range(len(sentences) - max_sentences + 1))

def extract_quotes_from_answer(answer):
    return re.findall(r'"(.*?)"', answer)

# ---------- GPT RESPONSE FUNCTION ----------
def get_response(query):
    response = engine.query(query)
    retrieved_chunks = response.source_nodes

    retrieved_text = "\n\n".join(node.node.get_content()
                                 for node in retrieved_chunks)
    candidate_quotes = set()
    for node in retrieved_chunks:
        chunk_text = node.node.get_content()
        candidate_quotes.update(extract_candidate_quotes(chunk_text))

    synthesis_prompt = (
        "Write a thoughtful, grounded response to the user’s question based on the following transcript excerpts. "
        "Your role is to serve as a knowledgeable, supportive peer — intelligent and concise, not robotic or verbose.\n\n"
        "Prioritize what is most relevant. Do not include information unless it directly helps answer the user’s question. "
        "Avoid padding the response with loosely connected details, even if present in the retrieved text.\n\n"
        "Use a warm, conversational tone that reflects an experienced facilitator — steady, precise, curious. "
        "Avoid “high school essay” structure or formulaic writing.\n\n"
        "Structure your response with:\n"
        "- A clear opening insight or framing reflection\n"
        "- A few key points, expressed in your own words\n"
        "- A short closing takeaway or reminder, if appropriate\n\n"
        "You may paraphrase, synthesize, or include short educator quotes (one or two sentences) when they help ground or illustrate the answer. "
        "Always use quotation marks and proper attribution. Do not copy and paste full transcript chunks or extended passages. "
        "Summarize and synthesize wherever possible. Never invent quotes or ideas.\n\n"
        "When paraphrasing or summarizing, identify the educator(s) behind the ideas whenever the source is clear. "
        "For example: 'According to Jason Foster...' or 'As Gina Gratza explains...'. "
        "This helps the user connect with the voices behind the guidance.\n\n"
        "Keep the answer brief if the question is simple or already complete.\n\n"
        f"User’s question: {query}\n\nTranscript excerpts:\n{retrieved_text}\n\nAnswer:"
    )

    answer = Settings.llm.complete(synthesis_prompt).text
    quotes_used = extract_quotes_from_answer(answer)
    invalid_quotes = [q for q in quotes_used if q not in candidate_quotes]

    if invalid_quotes:
        synthesis_prompt = (
            "Write a thoughtful, grounded response to the user’s question based on the following transcript excerpts. "
            "Your role is to serve as a knowledgeable, supportive peer — intelligent and concise, not robotic or verbose.\n\n"
            "Prioritize what is most relevant. Do not include information unless it directly helps answer the user’s question. "
            "Avoid padding the response with loosely connected details, even if present in the retrieved text.\n\n"
            "Use a warm, conversational tone that reflects an experienced facilitator — steady, precise, curious. "
            "Avoid “high school essay” structure or formulaic writing.\n\n"
            "Structure your response with:\n"
            "- A clear opening insight or framing reflection\n"
            "- A few key points, expressed in your own words\n"
            "- A short closing takeaway or reminder, if appropriate\n\n"
            "Do not include direct quotes. Summarize or paraphrase only. Never invent quotes or ideas.\n\n"
            "When paraphrasing or summarizing, identify the educator(s) behind the ideas whenever the source is clear. "
            "For example: 'According to Jason Foster...' or 'As Gina Gratza explains...'. "
            "This helps the user connect with the voices behind the guidance.\n\n"
            "Keep the answer brief if the question is simple or already complete.\n\n"
            f"User’s question: {query}\n\nTranscript excerpts:\n{retrieved_text}\n\nAnswer:"
        )
        answer = Settings.llm.complete(synthesis_prompt).text

    return answer.strip(), retrieved_chunks

# ---------- FASTAPI SETUP ----------
app = FastAPI()

# Root route for status check
@app.get("/")
def read_root():
    return {"message": "Trek GPT backend is live!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now, tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.post("/ask")
def ask_question(query: Query):
    answer, sources = get_response(query.question)
    source_list = [{
        "title": s.metadata.get("title", ""),
        "educator": s.metadata.get("educator", "")
    } for s in sources]
    return {"response": answer, "sources": source_list}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ---------- RUN APP ----------
