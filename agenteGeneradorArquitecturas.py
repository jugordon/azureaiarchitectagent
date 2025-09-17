import asyncio
from azure.identity.aio import AzureCliCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread

# Business requirement input
TASK = "Design an Azure architecture for a real-time analytics platform that ingests IoT data, processes it with Stream Analytics, stores it in SQL Database, and visualizes it using Power BI. Ensure secure access and scalability."

async def main() -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # Create agent with image generation tool
        agent_definition = await client.agents.create_agent(
            name="ArchitectureDiagramAgent",
            instructions=(
                "You are an expert Azure architect specialized in artificial intelligence solutions. Based on a business requirement, generate an arquitecture diagram of Draw.io (xml file) "
                "including services like Azure OpenAI, AI Foundry, AI Search, AI Services, Document intelligence, storage accounts, postgresql, and security components. "
                "Then generate the xml file of the representation of the architecture with a descriptive prompt. Make sure to diagram the connections or dependencies between the components." \
                "You can use reference architectures in Azure as a guide https://learn.microsoft.com/en-us/azure/architecture/browse/?azure_categories=ai-machine-learning"
            ),
            model=AzureAIAgentSettings().model_deployment_name,

        )

        # Create Semantic Kernel agent
        agent = AzureAIAgent(client=client, definition=agent_definition)

        # Create conversation thread
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# Business Requirement: '{TASK}'")
            async for response in agent.invoke(messages=TASK, thread=thread):
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

if __name__ == "__main__":
    asyncio.run(main())