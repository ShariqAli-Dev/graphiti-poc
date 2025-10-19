"""
Pydantic AI Agent for Graphiti Q&A

This agent uses Pydantic AI to provide natural language Q&A over the Graphiti knowledge graph.
Based on the graphiti-agent reference implementation.
"""

from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live
import asyncio
import os

# IMPORTANT: Load .env BEFORE importing graphiti_core
# graphiti_core reads SEMAPHORE_LIMIT at import time
load_dotenv()

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from graphiti_core import Graphiti


# ========== Dependencies ==========
@dataclass
class GraphitiDependencies:
    """Dependencies for the Graphiti agent."""
    graphiti_client: Graphiti


# ========== Model Configuration ==========
def get_model():
    """Configure and return the LLM model to use."""
    model_choice = os.getenv('MODEL_CHOICE', 'gpt-4o-mini')
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        raise ValueError(
            'OPENAI_API_KEY must be set in .env file. '
            'Please add your OpenAI API key to the .env file.'
        )

    return OpenAIModel(model_choice, provider=OpenAIProvider(api_key=api_key))


# ========== Create the Agent ==========
graphiti_agent = Agent(
    get_model(),
    system_prompt="""You are a helpful assistant with access to a knowledge graph filled with information from documents.

When the user asks you a question, use your search tool to query the knowledge graph and then answer honestly based on the facts you find.

Be willing to admit when you didn't find the information necessary to answer the question.

Synthesize information from multiple facts into a coherent, natural language answer.""",
    deps_type=GraphitiDependencies
)


# ========== Search Result Model ==========
class GraphitiSearchResult(BaseModel):
    """Model representing a search result from Graphiti."""
    uuid: str = Field(description="The unique identifier for this fact")
    fact: str = Field(description="The factual statement retrieved from the knowledge graph")
    valid_at: Optional[str] = Field(None, description="When this fact became valid (if known)")
    invalid_at: Optional[str] = Field(None, description="When this fact became invalid (if known)")
    source_node_uuid: Optional[str] = Field(None, description="UUID of the source node")


# ========== Graphiti Search Tool ==========
@graphiti_agent.tool
async def search_graphiti(ctx: RunContext[GraphitiDependencies], query: str) -> List[GraphitiSearchResult]:
    """Search the Graphiti knowledge graph with the given query.

    Args:
        ctx: The run context containing dependencies
        query: The search query to find information in the knowledge graph

    Returns:
        A list of search results containing facts that match the query
    """
    # Access the Graphiti client from dependencies
    graphiti = ctx.deps.graphiti_client

    try:
        # Perform the search
        results = await graphiti.search(query)

        # Format the results
        formatted_results = []
        for result in results:
            formatted_result = GraphitiSearchResult(
                uuid=result.uuid,
                fact=result.fact,
                source_node_uuid=result.source_node_uuid if hasattr(result, 'source_node_uuid') else None
            )

            # Add temporal information if available
            if hasattr(result, 'valid_at') and result.valid_at:
                formatted_result.valid_at = str(result.valid_at)
            if hasattr(result, 'invalid_at') and result.invalid_at:
                formatted_result.invalid_at = str(result.invalid_at)

            formatted_results.append(formatted_result)

        return formatted_results
    except Exception as e:
        print(f"Error searching Graphiti: {str(e)}")
        raise


# ========== Shared Agent Loop Function ==========
async def _agent_loop(graphiti_client: Graphiti, console: Console, exit_commands: list[str], return_message: str):
    """
    Shared agent interaction loop for both CLI and standalone modes.

    Args:
        graphiti_client: Initialized Graphiti client
        console: Rich console for rendering
        exit_commands: List of commands that exit the loop
        return_message: Message to display when exiting

    Returns:
        List of messages from the conversation
    """
    messages = []

    try:
        while True:
            # Get user input
            user_input = input("\n[You] ")

            # Check if user wants to exit
            if user_input.lower() in exit_commands:
                print(return_message)
                break

            if not user_input.strip():
                continue

            try:
                # Process the user input and output the response
                print("\n[Assistant]")
                with Live('', console=console, vertical_overflow='visible') as live:
                    # Pass the Graphiti client as a dependency
                    deps = GraphitiDependencies(graphiti_client=graphiti_client)

                    async with graphiti_agent.run_stream(
                        user_input, message_history=messages, deps=deps
                    ) as result:
                        curr_message = ""
                        async for message in result.stream_text(delta=True):
                            curr_message += message
                            live.update(Markdown(curr_message))

                        # Add the new messages to the chat history
                        messages.extend(result.all_messages())

            except Exception as e:
                print(f"\n[Error] An error occurred: {str(e)}")

    except KeyboardInterrupt:
        print(f"\n{return_message}")

    return messages


# ========== Main Interactive Agent Function ==========
async def run_interactive_agent(graphiti_client: Graphiti):
    """
    Run the Graphiti agent in interactive mode.

    Args:
        graphiti_client: Initialized Graphiti client
    """
    print("\n" + "="*80)
    print("GRAPHITI AI AGENT - Natural Language Q&A")
    print("="*80)
    print("\nAsk questions about your documents. Type 'exit' to return to main menu.\n")

    console = Console()
    await _agent_loop(
        graphiti_client,
        console,
        exit_commands=['exit', 'quit', 'back', 'bye'],
        return_message="Returning to main menu..."
    )


# ========== Standalone Mode ==========
async def main():
    """Run the agent as a standalone program."""
    print("Graphiti Agent - Powered by Pydantic AI")
    print("Enter 'exit' to quit the program.\n")

    # Neo4j connection parameters
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

    # Initialize Graphiti with Neo4j connection
    graphiti_client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

    # Initialize the graph database with graphiti's indices if needed
    try:
        await graphiti_client.build_indices_and_constraints()
        print("Graphiti indices ready.\n")
    except Exception as e:
        print(f"Note: {str(e)}\n")

    console = Console()

    try:
        # Use shared agent loop
        await _agent_loop(
            graphiti_client,
            console,
            exit_commands=['exit', 'quit', 'bye', 'goodbye'],
            return_message="Goodbye!"
        )
    finally:
        # Close the Graphiti connection when done
        await graphiti_client.close()
        print("\nGraphiti connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise
