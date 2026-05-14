from typing import Union
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langfuse import observe
from app.services.chat_service import ask_question
from app.services.entity_service import fuzzy_search_engine
from app.schemas.chat import QuestionRequest, ChatResponse, ErrorResponse

from app.core.clients import langfuse_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Fuzzy Search Engine and build indices before accepting requests
    print("Starting up: Initializing Fuzzy Search Engine...")
    fuzzy_search_engine.initialize()
    yield

app = FastAPI(
    title="FMCG Chat API",
    description="API for converting natural language FMCG questions into BigQuery SQL and executing them.",
    version="1.0.0",
    lifespan=lifespan
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

