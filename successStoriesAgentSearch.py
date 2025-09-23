import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from azure.ai.projects.models import ConnectionType

from azure.ai.agents.models import MessageRole, ListSortOrder

from dotenv import load_dotenv

load_dotenv()

# Retrieve the endpoint from environment variables

project_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")

# Initialize the AIProjectClient
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(exclude_interactive_browser_credential=False)
)

# Define the Azure AI Search connection ID and index name
azure_ai_conn_id = project_client.connections.get_default(ConnectionType.AZURE_AI_SEARCH).id

# find the index name in your AI Search Azure resource page under Search Management -> Indexes
index_name = "succcesstories"

# Initialize the Azure AI Search tool
ai_search = AzureAISearchTool(
    index_connection_id=azure_ai_conn_id,
    index_name=index_name,
    query_type=AzureAISearchQueryType.SIMPLE,  # Use SIMPLE query type
    top_k=3,  # Retrieve the top 3 results
    filter="",  # Optional filter for search results
)



# Create an agent with the Azure AI Search tool
agent = project_client.agents.create_agent(
    model=model_deployment_name,
    name="Success stories agent",
    instructions=f"""
    You are an expert Azure architect specialized in artificial intelligence solutions. Your role is to receive a business requirement and determine if there is any success story that can be helpful to provide information,
    for example to provide a related business goal, technology solution and which products ( Azure services ) were key to implement the solution.
    The success stories are stored in a Postgres database, you can use the provided tools to get accurate and up-to-date information.
    
    """,
    tools=ai_search.definitions,
    tool_resources=ai_search.resources,
)
print(f"Created agent, ID: {agent.id}")



# Create a thread for communication
thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

# Send a message to the thread
message = project_client.agents.messages.create(
    thread_id=thread.id,
    role=MessageRole.USER,
    content="Is there any success story related to AI solutions for a call center that involves knowledge mining and question answering?",
)
print(f"Created message, ID: {message['id']}")

# Create and process an agent run in the thread with tools
run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
print(f"Run finished with status: {run.status}")

# Fetch and log all messages exchanged during the conversation thread
messages = project_client.agents.messages.list(thread_id=thread.id)
for msg in messages:
    print(f"Message ID: {msg.id}, Role: {msg.role}, Content: {msg.content}")

# Delete the agent after use
project_client.agents.delete_agent(agent.id)   
print("Deleted agent")
