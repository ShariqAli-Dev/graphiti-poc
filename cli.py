"""
Graphiti CLI - Simplified Interface

Clean, menu-driven interface for managing documents in Graphiti.
Based on the graphiti-agent reference implementation.
"""

import asyncio
import logging
import os
import readline
import glob
from pathlib import Path

from dotenv import load_dotenv

# IMPORTANT: Load .env BEFORE importing graphiti_core
# graphiti_core reads SEMAPHORE_LIMIT at import time
load_dotenv()

from graphiti_core import Graphiti

from graphiti_manager import GraphitiManager
from agent import run_interactive_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


# ========== Tab Completion for File Paths ==========
def path_completer(text, state):
    """
    Tab completion function for file paths.

    This enables tab-completion when entering file or directory paths.
    """
    # Expand ~ and environment variables
    text = os.path.expanduser(text)
    text = os.path.expandvars(text)

    # If no path separator, search in current directory
    if '/' not in text:
        text = './' + text

    # Get directory and prefix
    dirname = os.path.dirname(text) or '.'
    prefix = os.path.basename(text)

    # Find matching paths
    try:
        matches = []
        for entry in os.listdir(dirname):
            if entry.startswith(prefix):
                full_path = os.path.join(dirname, entry)
                # Add trailing slash for directories
                if os.path.isdir(full_path):
                    matches.append(full_path + '/')
                else:
                    matches.append(full_path)

        # Return the state-th match
        if state < len(matches):
            # Clean up the path for display
            result = matches[state]
            # Remove leading ./ if present
            if result.startswith('./'):
                result = result[2:]
            return result
        else:
            return None
    except OSError:
        return None


def enable_tab_completion():
    """Enable tab completion for file paths."""
    # Set up tab completion
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(path_completer)


class GraphitiCLI:
    """Simplified CLI for Graphiti operations."""

    def __init__(self):
        """Initialize the CLI."""
        # Neo4j connection parameters
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

        if not self.neo4j_uri or not self.neo4j_user or not self.neo4j_password:
            raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in .env')

        self.graphiti = None
        self.manager = None

    async def initialize(self):
        """Initialize Graphiti connection."""
        logger.info("Connecting to Neo4j...")

        # Initialize Graphiti
        self.graphiti = Graphiti(self.neo4j_uri, self.neo4j_user, self.neo4j_password)

        # Build indices and constraints
        await self.graphiti.build_indices_and_constraints()

        # Initialize manager
        self.manager = GraphitiManager(self.graphiti)

        logger.info("Graphiti initialized successfully")

    async def cleanup(self):
        """Clean up resources."""
        if self.graphiti:
            await self.graphiti.close()
            logger.info("Connection closed")

    def display_menu(self):
        """Display the main menu."""
        print("\n" + "="*80)
        print("GRAPHITI KNOWLEDGE GRAPH - Document Manager")
        print("="*80)
        print("\n1. Upload File")
        print("2. Upload Directory")
        print("3. Search Graph (Raw Facts)")
        print("4. Ask Question (AI Agent)")
        print("5. List All Episodes")
        print("6. Reset Database")
        print("7. Exit")
        print("\n" + "="*80)

    async def upload_file(self):
        """Handle file upload."""
        print("\n" + "-"*80)
        print("UPLOAD FILE")
        print("-"*80)

        file_path = input("\nEnter file path: ").strip()

        if not file_path:
            print("File path cannot be empty")
            return

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        try:
            print(f"\nUploading {file_path}...")
            result = await self.manager.upload_file(file_path)

            print(f"\n✓ File uploaded successfully!")
            print(f"  Filename: {result['filename']}")
            print(f"  Episode UUID: {result['episode_uuid']}")
            print(f"  Word Count: {result['word_count']}")

        except Exception as e:
            print(f"\n✗ Upload failed: {e}")

        input("\nPress Enter to continue...")

    async def upload_directory(self):
        """Handle directory upload."""
        print("\n" + "-"*80)
        print("UPLOAD DIRECTORY")
        print("-"*80)

        dir_path = input("\nEnter directory path: ").strip()

        if not dir_path:
            print("Directory path cannot be empty")
            return

        if not os.path.exists(dir_path):
            print(f"Directory not found: {dir_path}")
            return

        try:
            # Get delay setting from environment
            delay_seconds = float(os.getenv('UPLOAD_DELAY_SECONDS', 0))

            print(f"\nScanning {dir_path}...")
            if delay_seconds > 0:
                print(f"Rate limiting: {delay_seconds}s delay between files")
                print("(Configure via UPLOAD_DELAY_SECONDS in .env)")

            results = await self.manager.upload_directory(dir_path, delay_seconds=delay_seconds)

            # Count successes and failures
            successes = [r for r in results if r.get('success')]
            failures = [r for r in results if not r.get('success')]

            print(f"\n{'='*80}")
            print(f"✓ Uploaded {len(successes)} files successfully")
            if failures:
                print(f"✗ Failed to upload {len(failures)} files")
            print(f"{'='*80}")

            # Show summary details
            if successes:
                print("\nSuccessful uploads:")
                for r in successes:
                    print(f"  - {r['filename']} ({r['word_count']} words)")

            if failures:
                print("\nFailed uploads:")
                for r in failures:
                    error_msg = r.get('error', 'Unknown error')
                    # Truncate long error messages
                    if len(error_msg) > 100:
                        error_msg = error_msg[:100] + "..."
                    print(f"  - {r['filename']}: {error_msg}")

        except Exception as e:
            print(f"\n✗ Directory upload failed: {e}")

        input("\nPress Enter to continue...")

    async def search_graph(self):
        """Handle graph search."""
        print("\n" + "-"*80)
        print("SEARCH KNOWLEDGE GRAPH")
        print("-"*80)

        query = input("\nEnter search query: ").strip()

        if not query:
            print("Query cannot be empty")
            return

        num_results = input("Number of results (default 10): ").strip()
        num_results = int(num_results) if num_results.isdigit() else 10

        try:
            print(f"\nSearching for: {query}")
            results = await self.manager.search(query, num_results)

            # Display results
            self.manager.display_search_results(results)

        except Exception as e:
            print(f"\n✗ Search failed: {e}")

        input("\nPress Enter to continue...")

    async def ask_agent(self):
        """Launch the AI agent for Q&A."""
        try:
            await run_interactive_agent(self.graphiti)
        except Exception as e:
            print(f"\n✗ Agent error: {e}")

    async def list_episodes(self):
        """List all episodes in the graph."""
        print("\n" + "-"*80)
        print("ALL EPISODES")
        print("-"*80)

        try:
            episodes = await self.manager.get_all_episodes()

            if not episodes:
                print("\nNo episodes found in the graph.")
            else:
                print(f"\nFound {len(episodes)} episodes:\n")
                for idx, ep in enumerate(episodes, 1):
                    print(f"{idx}. {ep.name}")
                    print(f"   UUID: {ep.uuid}")
                    print(f"   Created: {ep.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    content_preview = ep.content[:100] + "..." if len(ep.content) > 100 else ep.content
                    print(f"   Content: {content_preview}")
                    print()

        except Exception as e:
            print(f"\n✗ Failed to list episodes: {e}")

        input("\nPress Enter to continue...")

    async def reset_database(self):
        """Reset the database."""
        print("\n" + "-"*80)
        print("RESET DATABASE")
        print("-"*80)

        print("\n⚠️  WARNING: This will delete ALL data in your Neo4j database!")
        print("This action cannot be undone.")

        confirmation = input("\nType 'DELETE EVERYTHING' to confirm: ").strip()

        if confirmation != 'DELETE EVERYTHING':
            print("Reset cancelled")
            return

        try:
            print("\nClearing database...")
            await self.manager.clear_database()
            print("\n✓ Database reset successfully")

        except Exception as e:
            print(f"\n✗ Reset failed: {e}")

        input("\nPress Enter to continue...")

    async def run(self):
        """Run the main CLI loop."""
        try:
            # Enable tab completion for file paths
            enable_tab_completion()
            logger.info("Tab completion enabled for file paths")

            # Initialize
            await self.initialize()

            # Main loop
            while True:
                self.display_menu()
                choice = input("Select an option (1-7): ").strip()

                if choice == '1':
                    await self.upload_file()
                elif choice == '2':
                    await self.upload_directory()
                elif choice == '3':
                    await self.search_graph()
                elif choice == '4':
                    await self.ask_agent()
                elif choice == '5':
                    await self.list_episodes()
                elif choice == '6':
                    await self.reset_database()
                elif choice == '7':
                    print("\nGoodbye!")
                    break
                else:
                    print("\nInvalid selection. Please choose 1-7.")

        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user")
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    cli = GraphitiCLI()
    await cli.run()


if __name__ == '__main__':
    asyncio.run(main())
