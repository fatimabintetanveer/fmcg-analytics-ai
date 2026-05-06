from typing import Union
import traceback
from fastapi import FastAPI
from langfuse import observe
from app.services.chat_service import ask_question
from app.schemas.chat import QuestionRequest, ChatResponse, ErrorResponse, FeedbackRequest

from app.core.clients import langfuse_client

app = FastAPI(
    title="FMCG Chat API",
    description="API for converting natural language FMCG questions into BigQuery SQL and executing them.",
    version="1.0.0"
)

@app.post("/ask", response_model=Union[ChatResponse, ErrorResponse])
@observe(name="Ask Endpoint")
def ask_endpoint(payload: QuestionRequest):
    """
    Process a natural language question and return calculated metrics.
    """
    try:

        result = ask_question(payload.question, payload.org_id, payload.data_type_id, payload.reported_data_end)
        
        # Inject the trace ID into the response for the frontend
        if isinstance(result, dict) and "error" not in result:
            result["trace_id"] = langfuse_client.get_current_trace_id()
            
        return result
        
    except Exception as e:
        # Catch unexpected backend crashes and return a structured ErrorResponse
        return ErrorResponse(
            error="Backend Crash",
            details=str(e),
            traceback=traceback.format_exc(),
            message="An unexpected error occurred while processing your request."
        )

@app.post("/feedback")
def post_feedback(payload: FeedbackRequest):
    """
    Submits user feedback score to Langfuse.
    """
    langfuse_client.create_score(
        trace_id=payload.trace_id,
        name="user_feedback",
        value=payload.score,
        comment=payload.comment
    )
    langfuse_client.flush()
    return {"status": "success", "message": "Feedback submitted successfully"}