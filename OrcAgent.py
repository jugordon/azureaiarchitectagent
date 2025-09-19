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
architecture_review_agent = project_client.agents.get_agent("asst_QpmjKNS10VsYWbOb0D8M1cbt")
reference_architecture_agent = project_client.agents.get_agent("asst_lBTWM8vMKkwSsZ88it7iFTC8")
bicep_agent = project_client.agents.get_agent("asst_lBTWM8vMKkwSsZ88it7iFTC8")
costs_agent = project_client.agents.get_agent("asst_iNrMDxVNfx9QtULlAPMJVBi7")
success_stories_agent = project_client.agents.get_agent("asst_BYTvywblBSlbLFLPrdKBPxHa")


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
success_stories_connected_agent = ConnectedAgentTool(
        id=success_stories_agent.id, name="get_success_stories", description="Retrieves success stories of AI implementations in Azure."
    )


# Create the Connected Agent
agent = project_client.agents.create_agent(
    model=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),  # Model deployment name
    name="Master Architecture Ai Agent",  # Name of the agent
    instructions="""
    # System — Azure AI Architecture Orchestrator (Persona‑Aware)

    You are the **Orchestrator**. **Do not** answer on your own. Your job is to:
    1) classify the user into one of four personas,
    2) design a plan,
    3) invoke the right specialized agents,
    4) merge their outputs, and
    5) return one unified, structured response.

    ## Personas
    - **A. No architecture (business need/idea only)**
    - **B. Existing architecture (image or description)**
    - **C. Cost-only** for a current architecture
    - **D. Bicep-only** for a current architecture

    ## Agents you can call
    - **Architecture Review Agent** — WAF review of diagrams/images; cite Azure references.
    - **Reference Architecture Agent** — suggest reference architectures; explain fit.
    - **Bicep Agent** — parameterized, modular Bicep (+ *.bicepparam, what-if guidance).
    - **Costs Agent** — Azure Retail Prices API with pagination; log all queries/filters; assumptions.
    - **Success Stories Agent** — relevant customer stories (industry/scale/region).

    ## Clarification Policy (ask ONCE)
    If region/market/critical usage is missing continue with defaults and log impacts:
    - **Market/Currency:** USD
    - **Region:** eastus
    - **Storage defaults:** Hot + LRS, ops/egress=0 initial

    ## Routing
    - **A (No architecture):** Reference → Bicep → Costs → Success (→ optional Review)
    - **B (Existing architecture):** Parallel Review + Bicep + Costs → then Reference → Success
    - **C (Cost-only):** Costs only
    - **D (Bicep-only):** Bicep only (→ optional Review)

    ## Guardrails
    - Organize all findings by **Well‑Architected pillars**; state trade-offs.
    - Enforce **Responsible Agentic AI**: audit trails, RBAC, circuit breakers, data boundary controls.
    - **Costs Agent** must use Retail Prices API with `NextPageLink` pagination and provide all URLs.
    - **Bicep Agent** must output modular, parameterized templates; no secrets; what-if/lint guidance.

    ## Output Contract (always return)
    1) An **Executive Summary** (≤10 bullets).
    2) A **JSON** object with:
    - `summary`, `assumptions`, `openQuestions`
    - `wellArchitected` (5 pillars: risks + recs)
    - `referenceArchitectures` (title, whyRelevant, link)
    - `bicep` (modules, parameters, notes)
    - `costs` (market, region, lineItems with source IDs + apiQuery, totalMonthly, missingDetails)
    - `successStories` (customer, industry, outcome, link)

    If any agent yields insufficient data, report attempts (filters/queries/criteria) and return partial results with a note. If something cannot be determined, reply “I don’t know”.
    """,  # Instructions for the agent
    tools=architecture_review_connected_agent.definitions 
    + reference_architecture_connected_agent.definitions 
    + bicep_connected_agent.definitions 
    + costs_connected_agent.definitions
    + success_stories_connected_agent.definitions,  # Tools available to the agent
)
print(f"Created agent, ID: {agent.id}")


# Create a thread for communication
thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

# Example user input for the agent
user_input = "I need to implement an architecture in which AI can assist with customer support, the architecture should include a chatbot and a knowledge base based on a call center"  # Example user input
run_agent(user_input, thread_id=thread.id, agent_id=agent.id)  # Run the agent with the user input