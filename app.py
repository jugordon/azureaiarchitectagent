import os
import chainlit as cl
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole
from dotenv import load_dotenv
# Load environment variables from the .env file (if present)
load_dotenv()


project_endpoint = os.environ["AZURE_AI_AGENT_ENDPOINT"]
agent_id = os.environ["AZURE_AI_AGENT_ID"]
print(f"Project Endpoint: {project_endpoint}")
print(f"Agent ID: {agent_id}")

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

@cl.on_chat_start
def on_chat_start():
    # Initialize the user session with the thread ID if it doesn't exist
    if not cl.user_session.get("thread_id"):
        # Create a new thread for the user
        thread = project_client.agents.threads.create()

        # Set the thread ID in the user session
        cl.user_session.set("thread_id", thread.id)
        print(f"New Thread ID: {thread.id}")
              
@cl.on_message
async def main(message: cl.Message):
    
    # Get the thread ID from the user session
    thread_id = cl.user_session.get("thread_id")

    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread_id,
        role="user",  # Role of the message sender
        content=message.content,  # Message content
    )
    
     # Create and process agent run in thread with tools
    run = project_client.agents.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
    print(f"Run finished with status: {run.status}")

    # Check the status of the run and print the result
    if run.status == "failed":
        response = run.last_error
    elif run.status == "completed":
        last_msg = project_client.agents.messages.get_last_message_text_by_role(thread_id=thread_id, role=MessageRole.AGENT)
        if last_msg:
            response = last_msg.text.value

    # Send a response back to the user
    await cl.Message(
        content=response,
    ).send()

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Blob storage price",
            message="What is the price of Blob storage in Azure?",
            icon="/public/Picture2.png",
            ),

        cl.Starter(
            label="I want to implement a RAG project",
            message="Help me with a Retrieval-Augmented Generation (RAG) project.",
            icon="/public/Picture3.png",
            ),
        cl.Starter(
            label="Suitcase Shopping",
            message="Provide me a list of suitcases for my trip to Paris.",
            icon="/public/Picture4.png",
            ),
        cl.Starter(
            label="Restaurant Recommendations",
            message="Provide me 3 restaurants in Paris that have great pizza.",
            icon="/public/Picture5.png",
            )
        ]