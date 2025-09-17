# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with the 
    OpenAPI tool from the Azure Agents service using a synchronous client.
    To learn more about OpenAPI specs, visit https://learn.microsoft.com/openapi

USAGE:
    python openapi.py

    Before running the sample:

    pip install azure-ai-agents azure-identity jsonref

    Set these environment variables with your own values:
    1) PROJECT_ENDPOINT - the Azure AI Agents endpoint.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in
       the "Models + endpoints" tab in your Azure AI Foundry project.
"""
# <initialization>
# Import necessary libraries
import os
import jsonref
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import OpenApiTool, OpenApiAnonymousAuthDetails

from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")

# Initialize the project client using the endpoint and default credentials
with AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
) as project_client:
    # </initialization>

    # <weather_tool_setup>
    # --- Weather OpenAPI Tool Setup ---
    # Load the OpenAPI specification for the weather service from a local JSON file using jsonref to handle references
    with open(os.path.join(os.path.dirname(__file__), "azure_cost_management_openapi.json"), "r") as f:
        azure_cost_management_spec = jsonref.loads(f.read())
    # </weather_tool_setup>

    # Create Auth object for the OpenApiTool (note: using anonymous auth here; connection or managed identity requires additional setup)
    auth = OpenApiAnonymousAuthDetails()

    # Initialize the main OpenAPI tool definition for weather
    openapi_tool = OpenApiTool(
        name="get_weather", spec=azure_cost_management_spec, description="Allow to get the pricing of Azure services", auth=auth
    )

    # </countries_tool_setup>

    # <agent_creation>
    # --- Agent Creation ---
    # Create an agent configured with the combined OpenAPI tool definitions
    agent = project_client.agents.create_agent(
        model=model_deployment_name, # Specify the model deployment
        name="agenteCostos", # Give the agent a name
        instructions="""You are an Azure Retail Pricing Specialist. Your job is to accurately fetch, normalize, and present Azure retail pricing using the Azure Retail Prices API according to the OpenAPI 3.1 specification for:

            Base URL: https://prices.azure.com/api
            Endpoint: GET /retail/prices
            Key query parameters:

        $filter (OData), e.g. serviceName eq 'Cognitive Services'
        Optional (if supported by server): currencyCode (e.g., USD, EUR)
        You must be precise, handle pagination, return well‑structured outputs, and include the exact query you executed.""", # Define agent's role
        tools=openapi_tool.definitions, # Provide the list of tool definitions
    )
    print(f"Created agent, ID: {agent.id}")
    # </agent_creation>

    # <thread_management>
    # --- Thread Management ---
    # Create a new conversation thread for the interaction
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Create the initial user message in the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="Cual es el precio del servicio de Azure OpenAI en la region East US?",
    )
    print(f"Created message, ID: {message.id}")
    # </thread_management>

    # <message_processing>
    # --- Message Processing (Run Creation and Auto-processing) ---
    # Create and automatically process the run, handling tool calls internally
    # Note: This differs from the function_tool example where tool calls are handled manually
    run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")
    # </message_processing>

    # <tool_execution_loop> # Note: This section now processes completed steps, as create_and_process_run handles execution
    # --- Post-Run Step Analysis ---
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Retrieve the steps taken during the run for analysis
    run_steps = project_client.agents.runs_steps.list(thread_id=thread.id, run_id=run.id)

    # Loop through each step to display information
    for step in run_steps.data:
        print(f"Step {step['id']} status: {step['status']}")

        # Check if there are tool calls recorded in the step details
        step_details = step.get("step_details", {})
        tool_calls = step_details.get("tool_calls", [])

        if tool_calls:
            print("  Tool calls:")
            for call in tool_calls:
                print(f"    Tool Call ID: {call.get('id')}")
                print(f"    Type: {call.get('type')}")

                function_details = call.get("function", {})
                if function_details:
                    print(f"    Function name: {function_details.get('name')}")
        print() # Add an extra newline between steps for readability
    # </tool_execution_loop>

    # <cleanup>
    # --- Cleanup ---
    # Delete the agent resource to clean up
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    # Fetch and log all messages exchanged during the conversation thread
    messages = project_client.agents.messages.list(thread_id=thread.id)
    print(f"Messages: {messages}")
    # </cleanup>