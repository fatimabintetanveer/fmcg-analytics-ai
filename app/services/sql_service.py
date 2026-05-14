import logging
import json
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.core.config import settings
from app.schemas.sql import SQLResponse
from app.core.clients import langfuse_client, langfuse_handler
from langfuse import observe

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
    model_kwargs={"response_format": {"type": "json_object"}}
)

# Fetch System Prompt
SYSTEM_PROMPT = "Generate BigQuery SQL."
langfuse_prompt = None

if settings.USE_LOCAL_PROMPT:
    try:
        logger.info("Loading prompt from local file: prompts/sql_generation_prompt.md")
        with open("prompts/sql_generation_prompt.md", "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()
    except FileNotFoundError:
        logger.error("Local prompt file not found. Falling back to default.")
else:
    try:
        logger.info("Fetching prompt from Langfuse...")
        langfuse_prompt = langfuse_client.get_prompt("fmcg_sql_gen")
        SYSTEM_PROMPT = langfuse_prompt.get_langchain_prompt() 
    except Exception as e:
        logger.error(f"Failed to fetch prompt from Langfuse: {e}. Falling back to default.")

parser = PydanticOutputParser(pydantic_object=SQLResponse)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", "Query: {question}\n\nResolved Entities:\n{resolved_entities_str}\n\n{error_context}")
]).partial(
    format_instructions=parser.get_format_instructions()
)

chain = prompt | llm | parser

def generate_sql(question: str, org_id: int, data_type_id: int, reported_data_end: str, resolved_entities: dict, error_message: Optional[str] = None) -> SQLResponse:
    global SYSTEM_PROMPT
    try:
        # Live reload local prompt if enabled
        if settings.USE_LOCAL_PROMPT:
            try:
                with open("prompts/sql_generation_prompt.md", "r", encoding="utf-8") as f:
                    SYSTEM_PROMPT = f.read()
            except Exception as e:
                logger.error(f"Failed to reload local prompt: {e}")
        # Start the observation 
        with langfuse_client.start_as_current_observation(
            as_type="generation",
            name="generate_sql",
            prompt=langfuse_prompt 
        ) as span:

            error_context = ""
            if error_message:
                error_context = f"WARNING: Your previous SQL attempt failed with this BigQuery error:\n{error_message}\n\nPlease fix the query and ensure it adheres to the schema."
                logger.warning(f"Retrying SQL generation due to error: {error_message}")
                
            # Fetch and format organization-specific metadata from local JSON
            metadata = load_metadata(org_id)
            product_meta, geo_meta, measure_map, time_period_map, brands_list = format_metadata(metadata)

            # Inject resolved entities from Fuzzy Search Engine
            resolved_entities_str = json.dumps(resolved_entities, indent=2) if resolved_entities else "None detected."
            
            result = chain.invoke(
                {
                    "question": question, 
                    "org_id": org_id,
                    "data_type_id": data_type_id,
                    "data_source": settings.DATA_SOURCE,
                    "reported_data_end": reported_data_end,
                    "resolved_entities_str": resolved_entities_str,
                    "product_meta": product_meta,
                    "geo_meta": geo_meta,
                    "measure_map": measure_map,
                    "time_period_map": time_period_map,
                    "brands_list": brands_list,
                    "error_context": error_context
                },
                config={"callbacks": [langfuse_handler]}
            )

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


def load_metadata(org_id: int) -> dict:
    """Loads organizational metadata from local JSON file."""
    filepath = f"app/metadata/org_{org_id}_metadata.json"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Metadata file not found: {filepath}")
        return {}

def format_metadata(metadata: dict):
    """Formats JSON metadata into strings for the LLM prompt."""
    if not metadata:
        return "", "", "", "", ""
    
    product_meta = "\n".join([f"- {k} → {v}" for k, v in metadata.get("dimension_metadata", {}).get("product", {}).items()])
    geo_meta = "\n".join([f"- {k} → {v}" for k, v in metadata.get("dimension_metadata", {}).get("geography", {}).items()])
    measure_map = "\n".join([f"- {k} → {v}" for k, v in metadata.get("measure_map", {}).items()])
    time_period_map = "\n".join([f"- {k} → {v}" for k, v in metadata.get("time_period_map", {}).items()])
    brands_list = ", ".join([f'"{b}"' for b in metadata.get("brands", [])])
    
    return product_meta, geo_meta, measure_map, time_period_map, brands_list

# ==============================================================================
# UNUSED / PREVIOUS VERSIONS (KEPT FOR REFERENCE)
# ==============================================================================

# --- PREVIOUS LOCAL PROMPT LOADING ---
# try:
#     with open("prompts/sql_generation_prompt.md", "r", encoding="utf-8") as f:
#         SYSTEM_PROMPT = f.read()
# except FileNotFoundError:
#     logger.error("Could not find prompts/sql_generation_prompt.md")
#     SYSTEM_PROMPT = "Generate BigQuery SQL."
# -----------------------------------
# result = chain.invoke({
#     "question": question, 
#     "org_id": org_id,
#     "data_type_id": data_type_id,
#     "reported_data_end": reported_data_end,
#     "error_context": error_context
# })
# -----------------------------------

