import asyncio
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import BingCustomSearchTool

from azure.identity.aio import AzureCliCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import (
    AnnotationContent,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)

# Pregunta de ejemplo sobre el Well Architected Framework
TASK = "¿Cuáles son los cinco pilares del Well Architected Framework para Inteligencia Artificial y qué recomienda cada uno?"

async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result: {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call: {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")

async def main() -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):

        bing_custom_connection = await client.connections.get(name="bingjgcustom")
        conn_id = bing_custom_connection.id

        print(conn_id)

        configuration_name = "azureWAFAI"
        # Initialize Bing Custom Search tool with connection id and configuration name
        bing_custom_tool = BingCustomSearchTool(connection_id=conn_id, instance_name=configuration_name)


        # 3. Crear agente en Azure AI Agent Service
        agent_definition = await client.agents.create_agent(
            name="AzureWAFAgent",
            instructions="""You are an expert in Azure Well Architected Framework for AI, you are responsable for providing guidance, recommendations and best practices of Azure Architectures for 
            Artificial Intelligence workloads.""",
            model=AzureAIAgentSettings().model_deployment_name,
            tools=bing_custom_tool.definitions,
        )

        # 4. Crear agente Semantic Kernel
        agent = AzureAIAgent(client=client, definition=agent_definition)

        # 5. Crear hilo de conversación
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# Usuario: '{TASK}'")
            async for response in agent.invoke(
                messages=TASK, thread=thread, on_intermediate_message=handle_intermediate_steps
            ):
                print(f"# {response.name}: {response}")
                thread = response.thread

                # 6. Mostrar anotaciones de fuentes consultadas
                if any(isinstance(item, AnnotationContent) for item in response.items):
                    for annotation in response.items:
                        if isinstance(annotation, AnnotationContent):
                            print(
                                f"Fuente: {annotation.url}\n"
                                f"Texto citado: {annotation.quote}\n"
                                f"Índice: {annotation.start_index}-{annotation.end_index}\n"
                            )
        finally:
            # 7. Limpieza
            await thread.delete() if thread else None
            #await client.agents.delete_agent(agent.id)

if __name__ == "__main__":
    asyncio.run(main())