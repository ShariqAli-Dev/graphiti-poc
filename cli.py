"""
Graphiti Knowledge Graph CLI Tool
Interactive command-line interface for managing documents in a Graphiti knowledge graph.
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from graphiti_core import Graphiti
from episode_manager import EpisodeManager
from search_manager import SearchManager


class GraphitiCLI:
    """Interactive CLI for Graphiti knowledge graph management."""

    def __init__(self):
        """Initialize the CLI."""
        load_dotenv()

        # Get Neo4j credentials
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD')

        if not self.neo4j_password:
            raise ValueError('NEO4J_PASSWORD must be set in .env file')

        self.graphiti = None
        self.episode_manager = None
        self.search_manager = None

    async def initialize(self):
        """Initialize Graphiti connection and managers."""
        print("Initializing Graphiti...")
        self.graphiti = Graphiti(self.neo4j_uri, self.neo4j_user, self.neo4j_password)

        # Build indices if needed
        await self.graphiti.build_indices_and_constraints()

        self.episode_manager = EpisodeManager(self.graphiti)
        self.search_manager = SearchManager(self.graphiti)

        print("✓ Connected to Neo4j")
        print("✓ Graphiti initialized\n")

    async def close(self):
        """Close Graphiti connection."""
        if self.graphiti:
            await self.graphiti.close()
            print("\n✓ Connection closed")

    def display_menu(self):
        """Display the main menu."""
        print("\n" + "="*80)
        print(" " * 25 + "GRAPHITI KNOWLEDGE GRAPH CLI")
        print("="*80)
        print("\nFILE MANAGEMENT:")
        print("  1. Upload File(s)")
        print("  2. Delete File")
        print("  3. List All Files")
        print("  4. Show File Details")
        print("  5. Refresh File (Delete & Re-upload)")
        print("\nSEARCH:")
        print("  6. Search Knowledge Graph")
        print("\nDATABASE MANAGEMENT:")
        print("  7. Reset Database")
        print("  8. Cleanup Orphaned Entities")
        print("\nOTHER:")
        print("  9. Exit")
        print("="*80)

    async def upload_file(self):
        """Handle file upload."""
        print("\n" + "-"*80)
        print("UPLOAD FILE(S)")
        print("-"*80)

        file_path = input("\nEnter file path (or directory for bulk upload): ").strip()

        if not os.path.exists(file_path):
            print(f"Error: Path not found: {file_path}")
            return

        version = input("Enter version (optional, e.g., Q3_2024): ").strip() or None

        paths_to_upload = []

        if os.path.isdir(file_path):
            # Bulk upload directory
            print(f"\nScanning directory: {file_path}")
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    if file.endswith(('.pdf', '.docx', '.doc', '.txt', '.md', '.xlsx', '.xls')):
                        paths_to_upload.append(os.path.join(root, file))

            print(f"Found {len(paths_to_upload)} supported files")
            if not paths_to_upload:
                print("No supported files found")
                return

            confirm = input(f"Upload all {len(paths_to_upload)} files? (yes/no): ").strip().lower()
            if confirm != 'yes':
                return
        else:
            paths_to_upload = [file_path]

        # Upload files
        successful = 0
        failed = 0

        for path in paths_to_upload:
            try:
                print(f"\n{'='*80}")
                result = await self.episode_manager.upload_file(path, version)
                print(f"✓ Upload successful: {result['file_id']}")
                successful += 1
            except Exception as e:
                print(f"✗ Upload failed: {e}")
                failed += 1

        print(f"\n{'='*80}")
        print(f"Upload Summary: {successful} successful, {failed} failed")
        print(f"{'='*80}")

    async def delete_file(self):
        """Handle file deletion."""
        print("\n" + "-"*80)
        print("DELETE FILE")
        print("-"*80)

        file_id = input("\nEnter file ID to delete: ").strip()

        if not file_id:
            print("File ID cannot be empty")
            return

        confirm = input(f"Are you sure you want to delete '{file_id}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled")
            return

        try:
            result = await self.episode_manager.delete_file(file_id)
            print(f"\n✓ Deleted {result['deleted_count']} episodes for file: {file_id}")
        except Exception as e:
            print(f"✗ Deletion failed: {e}")

    async def list_files(self):
        """Handle file listing."""
        print("\n" + "-"*80)
        print("ALL FILES IN KNOWLEDGE GRAPH")
        print("-"*80)

        try:
            files = await self.episode_manager.list_files()

            if not files:
                print("\nNo files found in the knowledge graph")
                return

            # Group by classification
            by_classification = {}
            for file in files:
                classification = file.get('classification', 'UNCLASSIFIED')
                if classification not in by_classification:
                    by_classification[classification] = []
                by_classification[classification].append(file)

            # Display grouped files
            for classification in sorted(by_classification.keys()):
                print(f"\n{classification}:")
                print("-" * 80)

                for file in sorted(by_classification[classification], key=lambda f: f['file_id']):
                    print(f"\n  File ID: {file['file_id']}")
                    print(f"  Episodes: {file['episode_count']}")
                    if file.get('word_count'):
                        print(f"  Word Count: {file['word_count']}")
                    if file.get('upload_date'):
                        print(f"  Uploaded: {file['upload_date']}")

            print(f"\n{'='*80}")
            print(f"Total: {len(files)} files")
            print(f"{'='*80}")

        except Exception as e:
            print(f"✗ Failed to list files: {e}")

    async def show_file_details(self):
        """Handle showing file details."""
        print("\n" + "-"*80)
        print("FILE DETAILS")
        print("-"*80)

        file_id = input("\nEnter file ID: ").strip()

        if not file_id:
            print("File ID cannot be empty")
            return

        try:
            details = await self.episode_manager.get_file_details(file_id)

            if not details:
                print(f"No file found with ID: {file_id}")
                return

            print(f"\nFile ID: {details['file_id']}")
            print(f"Total Episodes: {details['total_episodes']}")

            if details['parent']:
                print(f"\nParent Episode:")
                print(f"  UUID: {details['parent']['uuid']}")
                print(f"  Name: {details['parent']['name']}")

            if details['sections']:
                print(f"\nSections ({len(details['sections'])}):")
                for section in details['sections']:
                    print(f"  {section['section_index'] + 1}. {section['section_name']}")
                    print(f"     UUID: {section['uuid']}")

        except Exception as e:
            print(f"✗ Failed to retrieve file details: {e}")

    async def refresh_file(self):
        """Handle file refresh (delete + re-upload)."""
        print("\n" + "-"*80)
        print("REFRESH FILE")
        print("-"*80)

        file_id = input("\nEnter file ID to refresh: ").strip()
        new_file_path = input("Enter path to new file version: ").strip()

        if not os.path.exists(new_file_path):
            print(f"Error: File not found: {new_file_path}")
            return

        version = input("Enter version (optional, e.g., Q4_2024): ").strip() or None

        confirm = input(f"This will delete '{file_id}' and upload '{new_file_path}'. Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Refresh cancelled")
            return

        try:
            # Delete old file
            print(f"\nDeleting old version...")
            await self.episode_manager.delete_file(file_id)

            # Upload new file
            print(f"\nUploading new version...")
            result = await self.episode_manager.upload_file(new_file_path, version)

            print(f"\n✓ File refreshed successfully: {result['file_id']}")

        except Exception as e:
            print(f"✗ Refresh failed: {e}")

    async def search_knowledge_graph(self):
        """Handle knowledge graph search."""
        print("\n" + "-"*80)
        print("SEARCH KNOWLEDGE GRAPH")
        print("-"*80)

        print("\nSearch Methods:")
        print("  1. Basic Hybrid Search (semantic + keyword)")
        print("  2. Center Node Search (reranked by graph distance)")
        print("  3. Node Search (find entities)")

        method = input("\nSelect search method (1-3): ").strip()

        if method not in ['1', '2', '3']:
            print("Invalid selection")
            return

        query = input("Enter search query: ").strip()
        if not query:
            print("Query cannot be empty")
            return

        num_results = input("Number of results (default 10): ").strip()
        num_results = int(num_results) if num_results.isdigit() else 10

        # Optional file filter
        filter_files = input("Filter by specific files? (yes/no): ").strip().lower()
        group_ids = None

        if filter_files == 'yes':
            file_ids = input("Enter file IDs (comma-separated): ").strip()
            group_ids = [fid.strip() for fid in file_ids.split(',') if fid.strip()]

        try:
            results = None

            if method == '1':
                # Basic Hybrid Search
                results = await self.search_manager.basic_hybrid_search(
                    query=query,
                    num_results=num_results,
                    group_ids=group_ids,
                )

            elif method == '2':
                # Center Node Search
                entity_name = input("Enter entity name for center node: ").strip()
                if not entity_name:
                    print("Entity name cannot be empty")
                    return

                # Find the node UUID
                center_uuid = await self.search_manager.get_node_for_search(entity_name)
                if not center_uuid:
                    print(f"Could not find entity: {entity_name}")
                    return

                results = await self.search_manager.center_node_search(
                    query=query,
                    center_node_uuid=center_uuid,
                    num_results=num_results,
                    group_ids=group_ids,
                )

            elif method == '3':
                # Node Search
                results = await self.search_manager.node_search(
                    query=query,
                    num_results=num_results,
                    group_ids=group_ids,
                )

            # Display results
            if results:
                self.search_manager.display_results(results)
            else:
                print("\nNo results found")

        except Exception as e:
            print(f"✗ Search failed: {e}")
            import traceback
            traceback.print_exc()

    async def reset_database(self):
        """Handle database reset."""
        print("\n" + "-"*80)
        print("RESET DATABASE")
        print("-"*80)
        print("\nWARNING: This will delete ALL nodes and relationships!")
        print("Indices and constraints will be preserved.")

        confirm = input("\nType 'DELETE EVERYTHING' to confirm: ").strip()

        if confirm != 'DELETE EVERYTHING':
            print("Reset cancelled")
            return

        try:
            print("\nDeleting all nodes and relationships...")

            # Use Neo4j driver to delete all data
            from graphiti_core.utils.maintenance.graph_data_operations import clear_data

            await clear_data(self.graphiti.driver)

            print("✓ Database reset complete")
            print("  All nodes and relationships have been deleted")
            print("  Indices and constraints are intact")

        except Exception as e:
            print(f"✗ Reset failed: {e}")

    async def cleanup_orphaned_entities(self):
        """Handle cleanup of orphaned entities."""
        print("\n" + "-"*80)
        print("CLEANUP ORPHANED ENTITIES")
        print("-"*80)
        print("\nThis will find and remove entities that are only referenced")
        print("by deleted episodes (no current episode connections).")

        confirm = input("\nProceed with cleanup? (yes/no): ").strip().lower()

        if confirm != 'yes':
            print("Cleanup cancelled")
            return

        try:
            print("\nScanning for orphaned entities...")

            # Query for orphaned nodes
            query = """
            MATCH (n:Entity)
            WHERE NOT EXISTS {
                MATCH (e:Episodic)-[:MENTIONS]->(n)
            }
            RETURN count(n) as orphan_count
            """

            result = await self.graphiti.driver.execute_query(query)
            orphan_count = result.records[0]['orphan_count'] if result.records else 0

            if orphan_count == 0:
                print("\n✓ No orphaned entities found")
                return

            print(f"\nFound {orphan_count} orphaned entities")
            confirm_delete = input("Delete these entities? (yes/no): ").strip().lower()

            if confirm_delete != 'yes':
                print("Cleanup cancelled")
                return

            # Delete orphaned entities
            delete_query = """
            MATCH (n:Entity)
            WHERE NOT EXISTS {
                MATCH (e:Episodic)-[:MENTIONS]->(n)
            }
            DETACH DELETE n
            RETURN count(n) as deleted_count
            """

            result = await self.graphiti.driver.execute_query(delete_query)
            deleted_count = result.records[0]['deleted_count'] if result.records else 0

            print(f"\n✓ Deleted {deleted_count} orphaned entities")

        except Exception as e:
            print(f"✗ Cleanup failed: {e}")

    async def run(self):
        """Run the CLI main loop."""
        try:
            await self.initialize()

            while True:
                self.display_menu()
                choice = input("\nEnter your choice (1-9): ").strip()

                if choice == '1':
                    await self.upload_file()
                elif choice == '2':
                    await self.delete_file()
                elif choice == '3':
                    await self.list_files()
                elif choice == '4':
                    await self.show_file_details()
                elif choice == '5':
                    await self.refresh_file()
                elif choice == '6':
                    await self.search_knowledge_graph()
                elif choice == '7':
                    await self.reset_database()
                elif choice == '8':
                    await self.cleanup_orphaned_entities()
                elif choice == '9':
                    print("\nExiting...")
                    break
                else:
                    print("\nInvalid choice. Please try again.")

        finally:
            await self.close()


async def main():
    """Main entry point."""
    cli = GraphitiCLI()
    await cli.run()


if __name__ == '__main__':
    asyncio.run(main())
