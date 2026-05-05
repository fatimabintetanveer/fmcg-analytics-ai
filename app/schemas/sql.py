from pydantic import BaseModel
from typing import Optional

class SQLResponse(BaseModel):
    numerator_query: str 
    denominator_query: Optional[str] = None
    query_type: str
