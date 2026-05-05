from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.core.constants import DEFAULT_REPORTED_DATA_END, DEFAULT_ORG_ID, DEFAULT_DATA_TYPE_ID

class QuestionRequest(BaseModel):
    question: str = Field(..., description="The natural language question asked by the user")
    org_id: int = Field(
        default=DEFAULT_ORG_ID,
        description="The organization ID"
    )
    data_type_id: int = Field(
        default=DEFAULT_DATA_TYPE_ID,
        description="The data type ID"
    )
    reported_data_end: str = Field(
        default=DEFAULT_REPORTED_DATA_END,
        description="The latest reported month to be used as context"
    )

class ChatResponse(BaseModel):
    numerator_sql: str
    denominator_sql: Optional[str] = None
    numerator_data: List[Dict[str, Any]]
    denominator_data: Optional[List[Dict[str, Any]]] = None
    calculated_results: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    error: str
    details: str
    message: Optional[str] = None
    traceback: Optional[str] = None
