# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.agents.models import BingGroundingTool,BingCustomSearchTool
from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import (
    AnnotationContent,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)

"""
The following sample demonstrates how to create an Azure AI agent that
uses the Bing grounding tool to answer a user's question.

Note: Please visit the following link to learn more about the Bing grounding tool:

https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding?tabs=python&pivots=overview
"""
#Example task
TASK = "I need an architecture for a artificial intelligence solution, my data source will be a call center, i need to perform knowledge mining and be able to answer questions about it"
bing_custom_name = "bingjgcustom"
bing_configuration_name = "referencheArchitecturesAI"


async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main() -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Enter your Bing Grounding Connection Name
        bing_connection = await client.connections.get(name=bing_custom_name)
        conn_id = bing_connection.id

        # 2. Initialize agent bing tool and add the connection id
        bing_grounding = BingCustomSearchTool(connection_id=conn_id,instance_name=bing_configuration_name)

        # 3. Create an agent with Bing grounding on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            name="ReferenceArchitectureAgent",
            instructions="""You are an expert Azure architect specialized in artificial intelligence solutions. Your role is to receive a business requirement and determine if there is any existing reference architecture 
            from official Azure documentation that can be applied to meet that requirement. Be sure to identify and suggest the most relevant architecture and explain what could be the modifications needed for the requirement of the user. 
            The official documentation of Azure Rerefence Architectures is this : https://learn.microsoft.com/en-us/azure/architecture/browse/?azure_categories=ai-machine-learning""",
            model=AzureAIAgentSettings().model_deployment_name,
            tools=bing_grounding.definitions,
        )

        # 4. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 6. Invoke the agent for the specified thread for response
            async for response in agent.invoke(
                messages=TASK, thread=thread, on_intermediate_message=handle_intermediate_steps
            ):
                print(f"# {response.name}: {response}")
                thread = response.thread

                # 7. Show annotations
                if any(isinstance(item, AnnotationContent) for item in response.items):
                    for annotation in response.items:
                        if isinstance(annotation, AnnotationContent):
                            print(
                                f"Annotation :> {annotation.url}, source={annotation.quote}, with "
                                f"start_index={annotation.start_index} and end_index={annotation.end_index}"
                            )
        finally:
            # 8. Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            #await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())