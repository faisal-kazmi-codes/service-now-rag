"""Chat / ask route."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import answer_question

router = APIRouter()


class AskBody(BaseModel):
    question: str
    top_k: int = 10


@router.post("/ask")
def ask_route(body: AskBody):
    """Ask a question; RAG search over Pinecone + in-memory store, answer via OpenAI. Run POST /sync/servicenow first."""
    return answer_question(question=body.question, top_k=body.top_k)
