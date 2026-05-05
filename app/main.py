from typing import Union
import traceback
from fastapi import FastAPI
from app.services.chat_service import ask_question
from app.schemas.chat import QuestionRequest, ChatResponse, ErrorResponse

app = FastAPI(
    title="FMCG Chat API",
    description="API for converting natural language FMCG questions into BigQuery SQL and executing them.",
    version="1.0.0"
)

@app.post("/ask", response_model=Union[ChatResponse, ErrorResponse])
def ask_endpoint(payload: QuestionRequest):
    """
    Process a natural language question and return calculated metrics.
    """
    try:
        result = ask_question(payload.question, payload.org_id, payload.data_type_id, payload.reported_data_end)
        return result
        
    except Exception as e:
        # Catch unexpected backend crashes and return a structured ErrorResponse
        return ErrorResponse(
            error="Backend Crash",
            details=str(e),
            traceback=traceback.format_exc(),
            message="An unexpected error occurred while processing your request."
        )