import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import json
from typing import Any, Callable, Set
from sqlalchemy import create_engine
from azure.ai.agents.telemetry import trace_function
from opentelemetry import trace

# Load environment variables
load_dotenv(".env")
CONN_STR = os.getenv("AZURE_PG_CONNECTION")

# The trace_func decorator will trace the function call and enable adding additional attributes
# to the span in the function implementation. Note that this will trace the function parameters and their values.

# Get data from the Postgres database
def vector_search_success_stories(vector_search_query: str, limit: int = 10) -> str:
    """
    Fetches the success stories of implementations of AI projects in Azure.

    :param query(str): The query to fetch success stories that are relevant for the user.
    :type query: str
    :param limit: The maximum number of cases to fetch, defaults to 10
    :type limit: int, optional

    :return: success story as a JSON string.
    :rtype: str
    """
        
    db = create_engine(CONN_STR)
    
    query = """
    SELECT story_id, story_title, business_goal, 
    embedding_desc <=> azure_openai.create_embeddings(
    'text-embedding-ada-002', %s)::vector as similarity
    FROM kwbase.success_stories
    ORDER BY similarity
    LIMIT %s;
    """

    print(f"query: {query}")
    
    # Fetch cases information from the database
    df = pd.read_sql(query, db, params=(vector_search_query,limit))

    # Adding attributes to the current span
    span = trace.get_current_span()
    span.set_attribute("requested_query", query)

    cases_json = json.dumps(df.to_json(orient="records"))
    span.set_attribute("cases_json", cases_json)
    return cases_json


# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    vector_search_success_stories
}