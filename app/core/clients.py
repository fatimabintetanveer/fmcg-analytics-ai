from google.cloud import bigquery
from langfuse import Langfuse
from app.core.config import settings

import os

# Initialize Langfuse Client
langfuse_client = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)

# Inject Google Application Credentials into the system environment for implicit auth
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

# Initialize BigQuery Client
bq_client = bigquery.Client()

def run_query(sql: str):
    """Executes a SQL query on BigQuery and returns the results as a list of dicts."""
    query_job = bq_client.query(sql)
    results = query_job.result()  
    rows = [dict(row) for row in results]
    return rows
