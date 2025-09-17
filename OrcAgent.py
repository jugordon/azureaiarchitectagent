import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, ConnectedAgentTool
from dotenv import load_dotenv

load_dotenv()


# Create an Azure AI Client from an endpoint, copied from your Azure AI Foundry project.
# You need to login to Azure subscription via Azure CLI and set the environment variables
project_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")  # Ensure the PROJECT_ENDPOINT environment variable is set

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

def run_agent(user_input, thread_id, agent_id):
    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread_id,  # ID of the thread to which the message belongs
        role="user",  # Role of the message sender
        content=user_input,  # Message content
    )
    print(f"Created message, ID: {message['id']}")

     # Create and process agent run in thread with tools
    run = project_client.agents.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
    print(f"Run finished with status: {run.status}")

    # Check the status of the run and print the result
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    elif run.status == "completed":
        last_msg = project_client.agents.messages.get_last_message_text_by_role(thread_id=thread_id, role=MessageRole.AGENT)
        if last_msg:
            print(f"Agent Response: {last_msg.text.value}")


#Setup the Connected Agent Tools
# Get the agent by its ID
waf_ai_agent = project_client.agents.get_agent("asst_Gfk7LgFKGIC9JsHqaIl7r9GP")
architecture_review_agent = project_client.agents.get_agent("asst_Gfk7LgFKGIC9JsHqaIl7r9GP")
reference_architecture_agent = project_client.agents.get_agent("asst_by5D8yYV4QTI7wAXoiSPirMC")
bicep_agent = project_client.agents.get_agent("asst_Gfk7LgFKGIC9JsHqaIl7r9GP")
costs_agent = project_client.agents.get_agent("asst_yPQUnAV3aygKdzZxI1X4y1J0")

waf_connected_agent = ConnectedAgentTool(
        id=waf_ai_agent.id, name="get_waf_info", description="Searches for information about WAF."
    )
architecture_review_connected_agent = ConnectedAgentTool(
        id=architecture_review_agent.id, name="get_architecture_review", description="Retrieves architecture review information."
    )
reference_architecture_connected_agent = ConnectedAgentTool(
        id=reference_architecture_agent.id, name="get_reference_architecture", description="Retrieves reference architecture information."
    )
bicep_connected_agent = ConnectedAgentTool(
        id=bicep_agent.id, name="get_bicep_templates", description="Retrieves Bicep template information."
    )
costs_connected_agent = ConnectedAgentTool(
        id=costs_agent.id, name="get_cost_estimates", description="Provides cost estimates for Azure resources."
    )


# Create the Connected Agent
agent = project_client.agents.create_agent(
    model=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),  # Model deployment name
    name="architecture-ai-agent",  # Name of the agent
    instructions="""
    You are an agent that coordinates Azure AI architecture tasks.
    Do not answer questions on your own.
    Your role is to be an orchestrator who will call the appropriate functions provided to you.
    Each function you have available is an agent that can accomplish a specific task.
        
        Here are descriptions of the tools you have available:
            - WAF Agent: An agent that provides information about the Azure Well-Architected Framework.
            - Architecture Review Agent: An agent that analyzes an existing architecture image and provides feedback based on the Azure Well-Architected Framework for AI and official Azure reference architectures.
            - Reference Architecture Agent: An agent that retrieves reference architecture information.
            - Bicep Agent: An agent that generates a parameterized Bicep deployment template based on the architecture image.
            - Costs Agent: An agent that produces a cost calculator based on the architecture image, considering SKUs, usage, and regional pricing.


        Use the tools to gather information and provide a comprehensive response to the user.
        If you are unable to answer the question, please respond with "I don't know".
    """,  # Instructions for the agent
    tools=waf_connected_agent.definitions 
    + architecture_review_connected_agent.definitions 
    + reference_architecture_connected_agent.definitions 
    + bicep_connected_agent.definitions 
    + costs_connected_agent.definitions,  # Tools available to the agent
)
print(f"Created agent, ID: {agent.id}")


# Create a thread for communication
thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

# Example user input for the agent
user_input = "What is the weather in Paris?"  # Example user input
run_agent(user_input, thread_id=thread.id, agent_id=agent.id)  # Run the agent with the user input