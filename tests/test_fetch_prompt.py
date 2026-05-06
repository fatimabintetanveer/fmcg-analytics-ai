import os
import sys

# Add the project root to sys.path to allow importing from 'app'
sys.path.append(os.getcwd())

from langfuse import get_client
from app.core.config import settings

os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL

langfuse = get_client()

try:
    prompt = langfuse.get_prompt("fmcg_sql_gen")
    print(f"Prompt type: {type(prompt)}")
    
    # Try to get the langchain prompt
    try:
        lc_prompt = prompt.get_langchain_prompt()
        print(f"Langchain prompt type: {type(lc_prompt)}")
        print(f"Input variables: {lc_prompt.input_variables}")
    except Exception as e:
        print(f"Failed to get langchain prompt: {e}")
        
except Exception as e:
    print(f"Failed to fetch prompt: {e}")
