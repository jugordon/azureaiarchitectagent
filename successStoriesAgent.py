# %%
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool,ToolSet
from datetime import datetime
from pg_agent_tools import user_functions
from dotenv import load_dotenv
# Load environment variables
load_dotenv(".env")

# Create an Azure AI Client from a connection string, copied from your Azure AI Foundry project.
# It should be in the format "<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<HubName>"
# Customers need to login to Azure subscription via Azure CLI and set the environment variables
project_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")  # Ensure the PROJECT_ENDPOINT environment variable is set

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

# Initialize agent toolset with user functions
functions = FunctionTool(user_functions)
toolset = ToolSet()
toolset.add(functions)

project_client.agents.enable_auto_function_calls(toolset)

agent = project_client.agents.create_agent(
    model= os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"), 
    name=f"Success stories agent",
    description="Success stories expert Agent", 
    instructions=f"""
    You are an expert Azure architect specialized in artificial intelligence solutions. Your role is to receive a business requirement and determine if there is any success story that can be helpful to provide information,
    for example to provide a related business goal, technology solution and which products ( Azure services ) were key to implement the solution.
    The success stories are stored in a Postgres database, you can use the provided tools to get accurate and up-to-date information.
    
    """, 
    toolset=toolset
)
print(f"Created agent, ID: {agent.id}")

# Create a thread for communication
thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

# Create a message to thread
message = project_client.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="I need to build an AI solution for a call center, I need to be able to perform knowledge mining and be able to answer questions about it, can you provide me with any success stories that could be helpful?",
)

print(f"Created message, ID: {message.id}")



from pprint import pprint

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

