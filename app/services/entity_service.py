import json
import time
import logging
from typing import List, Optional, Any

from rapidfuzz import fuzz, process
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.core.config import settings
from app.core.clients import langfuse_client, langfuse_handler
from app.schemas.chat import EntityExtraction
from langfuse import observe

logger = logging.getLogger(__name__)

class LLMEntityExtractor:
    """
    Extract entities from user query
    """
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        self.parser = PydanticOutputParser(pydantic_object=EntityExtraction)
        self.langfuse_prompt_obj: Optional[Any] = None
        
        try:
            logger.info("Fetching entity extraction prompt from Langfuse...")
            langfuse_prompt = langfuse_client.get_prompt("fmcg_entity_extraction")
            system_prompt = langfuse_prompt.get_langchain_prompt()
            self.langfuse_prompt_obj = langfuse_prompt
        except Exception as e:
            logger.error(f"Failed to fetch prompt from Langfuse: {e}")
            system_prompt = "Extract Product and Geography entities."
            self.langfuse_prompt_obj = None

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Query: {query}")
        ]).partial(
            format_instructions=self.parser.get_format_instructions()
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def extract(self, query: str) -> EntityExtraction:
        try:
            callbacks = [langfuse_handler] if langfuse_handler else []
            return self.chain.invoke(
                {"query": query, "user_query": query},
                config={"callbacks": callbacks}
            )
        except Exception as e:
            logger.error(f"LLM Extraction failed: {e}")
            return EntityExtraction(product_entities=[], geography_entities=[])


class FuzzySearchEngine:
    def __init__(self):
        self.product_index = None
        self.geography_index = None
        self.extractor: Optional[LLMEntityExtractor] = None

    # Load + Index
    def initialize(self):
        logger.info("--- Initializing Fuzzy Search Engine ---")
        start = time.time()

        self.extractor = LLMEntityExtractor()

        # Build indices that map raw attribute values to their column levels
        self.product_index = self._build_index(
            "epos_product.json",
            [('ph_5', 'Brand'), ('ph_2', 'Category'), ('ph_13', 'Packsize')]
        )

        self.geography_index = self._build_index(
            "epos_geography.json",
            [('h1_2', 'Channel'), ('h1_3', 'Region'),
             ('h1_4', 'Retailer'), ('h1_5', 'Country'), ('h1_6', 'City')]
        )

        logger.info(f"Initialized Fuzzy Search Engine in {time.time() - start:.2f}s")

    def _build_index(self, file, mappings):
        """
        Parses JSON to build a vocabulary of known entities and mapping 
        them to their metadata levels (e.g., Brand, Channel).
        """
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Metadata file not found: {file}")
            return {"raw": [], "raw_to_level": {}}

        raw_to_level = {}

        for row in data:
            for col, level in mappings:
                val = row.get(col)
                if val:
                    val = str(val).upper().strip()
                    if val not in raw_to_level:
                        raw_to_level[val] = level

        return {
            "raw": list(raw_to_level.keys()),
            "raw_to_level": raw_to_level
        }

    # Search
    def search(self, entity_list: List[str], index: dict) -> List[dict]:
        """
        Fuzzy matches extracted entities against the indexed vocabulary.
        """
        results = []
        raw_vocab = index["raw"]
        raw_to_level = index["raw_to_level"]

        if not raw_vocab:
            return results

        for entity in entity_list:
            q = entity.upper().strip()
            
            best = process.extractOne(q, raw_vocab, scorer=fuzz.WRatio)
            
            if best:
                matched_str = best[0]
                score = float(best[1])
                if score >= 85.0:
                    results.append({
                        "input": entity,
                        "matched": matched_str,
                        "score": round(score / 100, 2),
                        "level": raw_to_level.get(matched_str, "Unknown")
                    })
        
        return sorted(results, key=lambda x: x["score"], reverse=True)

    # Pipeline
    @observe(as_type="span", name="fuzzy_entity_search")
    def run(self, query: str) -> dict:
        logger.info(f"QUERY for Fuzzy Search Engine: {query}")

        # Guard clause to ensure engine was initialized at startup and satisfy type checkers
        if not self.extractor or self.product_index is None or self.geography_index is None:
            logger.error("Fuzzy Search Engine failed to initialize properly.")
            return {"product_results": [], "geography_results": []}

        # 1. LLM Extraction
        logger.info("Extracting entities via LLM...")
        extracted = self.extractor.extract(query)
        logger.debug(f"LLM Output: {extracted.model_dump_json(indent=2)}")

        # 2. Optimized Search: Product in Product Index, Geography in Geography Index
        product_results = self.search(extracted.product_entities, self.product_index)
        geo_results = self.search(extracted.geography_entities, self.geography_index)

        # 3. Format Output
        output = {
            "product_results": product_results,
            "geography_results": geo_results
        }

        logger.info("FINAL DETERMINISTIC OUTPUT computed.")
        logger.debug(json.dumps(output, indent=2))
        
        return output

# Create a global instance 
fuzzy_search_engine = FuzzySearchEngine()

if __name__ == "__main__":
    # Configure basic logging for the test run
    logging.basicConfig(level=logging.INFO)
    
    fuzzy_search_engine.initialize()
    
    test_query = "What is the market share of goody 200g Caned mushrooms in the MT channel?"
    
    print("\n" + "="*50)
    print(f"TESTING QUERY: {test_query}")
    print("="*50 + "\n")
    
    result = fuzzy_search_engine.run(test_query)
    
    print("\n" + "="*50)
    print("FINAL EXTRACTED & MATCHED RESULT:")
    print("="*50)
    print(json.dumps(result, indent=2))
