import os
import json
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from azure.ai.agents.telemetry import trace_function
from opentelemetry import trace
import logging
import azure.functions as func

# Load environment variables
load_dotenv(".env")
CONN_STR = os.getenv("AZURE_PG_CONNECTION")

@trace_function
def main(msg: func.QueueMessage) -> str:
    """
    Azure Function triggered by Azure Storage Queue.
    Fetches success stories from a PostgreSQL database based on a vector search query.

    :param msg: Queue message containing 'vector_search_query' and 'limit'
    :type msg: func.QueueMessage

    :return: JSON string of success stories
    :rtype: str
    """
    try:
        # Parse message body
        message_body = msg.get_body().decode('utf-8')
        message_json = json.loads(message_body)
        vector_search_query = message_json.get("vector_search_query", "")
        limit = int(message_json.get("limit", 10))

        # Connect to PostgreSQL
        db = create_engine(CONN_STR)

        # SQL query
        query = """
        SELECT story_id, story_title, business_goal, 
        embedding_desc <=> azure_openai.create_embeddings(
        'text-embedding-ada-002', %s)::vector as similarity
        FROM kwbase.success_stories
        ORDER BY similarity
        LIMIT %s;
        """

        # Execute query
        df = pd.read_sql(query, db, params=(vector_search_query, limit))

        # Add tracing attributes
        span = trace.get_current_span()
        span.set_attribute("requested_query", query)
        cases_json = json.dumps(df.to_json(orient="records"))
        span.set_attribute("cases_json", cases_json)

        return cases_json

    except Exception as e:
        logging.error(f"Error processing queue message: {e}")
        return json.dumps({"error": str(e)})