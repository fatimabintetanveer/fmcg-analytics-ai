import logging
import json
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.core.config import settings
from app.schemas.sql import SQLResponse

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
    model_kwargs={"response_format": {"type": "json_object"}}
)

# Load System Prompt
try:
    with open("prompts/sql_generation_prompt.md", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    logger.error("Could not find prompts/sql_generation_prompt.md")
    SYSTEM_PROMPT = "Generate BigQuery SQL."

parser = PydanticOutputParser(pydantic_object=SQLResponse)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", "{question}\n\n{error_context}")
]).partial(
    format_instructions=parser.get_format_instructions()
)

chain = prompt | llm | parser

def load_metadata(org_id: int):
    filepath = f"app/metadata/org_{org_id}_metadata.json"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Metadata file not found: {filepath}")
        return None

def format_metadata(metadata: dict):
    if not metadata:
        return "", "", "", "", ""
    
    product_meta = "\n".join([f"- {k} → {v}" for k, v in metadata.get("dimension_metadata", {}).get("product", {}).items()])
    geo_meta = "\n".join([f"- {k} → {v}" for k, v in metadata.get("dimension_metadata", {}).get("geography", {}).items()])
    measure_map = "\n".join([f"- {k} → {v}" for k, v in metadata.get("measure_map", {}).items()])
    time_period_map = "\n".join([f"- {k} → {v}" for k, v in metadata.get("time_period_map", {}).items()])
    brands_list = ", ".join([f"'{b}'" for b in metadata.get("brands", [])])
    
    return product_meta, geo_meta, measure_map, time_period_map, brands_list

def generate_sql(question: str, org_id: int, data_type_id: int, reported_data_end: str, error_message: Optional[str] = None) -> SQLResponse:
    try:
        error_context = ""
        if error_message:
            error_context = f"WARNING: Your previous SQL attempt failed with this BigQuery error:\n{error_message}\n\nPlease fix the query and ensure it adheres to the schema."
            logger.warning(f"Retrying SQL generation due to error: {error_message}")
            
#         metadata = load_metadata(org_id)
#         product_meta, geo_meta, measure_map, time_period_map, brands_list = format_metadata(metadata)
# 
#         result = chain.invoke({
#             "question": question, 
#             "org_id": org_id,
#             "data_type_id": data_type_id,
#             "reported_data_end": reported_data_end,
#             "error_context": error_context,
#             "data_source": settings.DATA_SOURCE,
#             "product_metadata": product_meta,
#             "geography_metadata": geo_meta,
#             "measure_map": measure_map,
#             "time_period_map": time_period_map,
#             "brands_list": brands_list
#         })

        # --- PREVIOUS VERSION ---
        result = chain.invoke({
            "question": question, 
            "org_id": org_id,
            "data_type_id": data_type_id,
            "reported_data_end": reported_data_end,
            "error_context": error_context
        })

        if settings.DEBUG:
            logger.info(f"\nQUESTION: {question}")
            logger.info(f"OUTPUT: {result}")

        return result

    except Exception as e:
        logger.error(f"ERROR in generate_sql: {e}")
        return SQLResponse(
            numerator_query="",
            denominator_query=None,
            query_type="unknown"
        )
