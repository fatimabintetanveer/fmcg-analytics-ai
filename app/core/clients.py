from google.cloud import bigquery
from langfuse import Langfuse
from app.core.config import settings
from langfuse import get_client, observe
from langfuse.langchain import CallbackHandler
import os

# Set environment variables for Langfuse
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL 

# Initialize Langfuse Client explicitly with credentials
langfuse_client = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL
)

# Initialize Langfuse Callback Handler 
langfuse_handler = CallbackHandler()


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

# Initialize BigQuery Client
bq_client = bigquery.Client()

@observe(as_type="span")
def run_query(sql: str):
    """Executes a SQL query on BigQuery and returns the results as a list of dicts."""
    query_job = bq_client.query(sql)
    results = query_job.result()  
    rows = [dict(row) for row in results]
    return rows
