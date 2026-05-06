from langfuse import get_client
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
import os

os.environ["LANGFUSE_DEBUG"] = "false"

def test_simple_connection():
    # Set env vars
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL  

    langfuse = get_client()

    # Create a trace using context manager
    with langfuse.start_as_current_observation(
        as_type="span",
        name="direct-connection-test"
    ) as span:
        span.update(output="Success!")

    langfuse.flush()

    print("✅ Direct Trace sent! Check dashboard.")

def test_callback_connection():
    # Set env vars
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL

    # Initialize CallbackHandler
    handler = CallbackHandler()

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY
    )

    print("Invoking LLM with Langfuse callback...")
    response = llm.invoke(
        [HumanMessage(content="Hello Langfuse!")],
        config={"callbacks": [handler]}
    )
    
    print(f"LLM Response: {response.content}")
    print("✅ Callback Trace sent! Check dashboard.")

if __name__ == "__main__":
    print("--- Testing Direct Client ---")
    test_simple_connection()
    print("\n--- Testing LangChain Callback ---")
    test_callback_connection()