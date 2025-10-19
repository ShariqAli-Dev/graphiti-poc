"""
Simplified Graphiti Manager

This module provides a clean interface for managing documents in Graphiti.
Based on the graphiti-agent reference implementation.

Key principles:
- One episode per file (no complex hierarchies)
- Direct Graphiti API usage (no unnecessary wrappers)
- Let Graphiti handle entity extraction and deduplication
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

from file_parsers import parse_file
from entity_types import entity_types

logger = logging.getLogger(__name__)


def extract_metadata_from_path(file_path: str) -> Dict[str, Optional[str]]:
    """
    Extract client and classification metadata from file path.

    Expected structure: .../client_name/classification_folder/document.ext
    Example: inputs/tener/TC103/Q1_2024_Report.txt

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with 'client' and 'classification' keys
        Returns None for missing values

    Note: This is a best-effort extraction. For ambiguous paths, you may need
    to manually specify client/classification metadata.
    """
    path = Path(file_path).resolve()
    parts = path.parts

    # Try to find the pattern: client/classification/file
    # Start from the end and work backwards
    if len(parts) >= 3:
        # parts[-1] is the filename
        # parts[-2] should be classification folder (e.g., TC103)
        # parts[-3] should be client folder (e.g., tener)
        classification = parts[-2]
        client = parts[-3]

        # Skip system/common directories that are unlikely to be client names
        # This prevents extracting "/home/user/projects" as client names
        skip_dirs = {'home', 'usr', 'var', 'tmp', 'etc', 'opt', 'bin', 'lib'}

        # Also skip common project structure directories
        # Note: If your client is actually named "projects" or "sandbox",
        # you'll need to adjust this logic or use a deeper directory structure
        skip_project_dirs = {'projects', 'sandbox', 'graphiti'}

        # Only skip if BOTH client and classification are in skip lists
        # This allows "inputs/TC103/file.pdf" to still extract TC103 as classification
        client_is_system = client.lower() in skip_dirs or client.lower() in skip_project_dirs
        classification_is_system = classification.lower() in skip_dirs

        # If client looks like a system directory, try going one level deeper
        if client_is_system and len(parts) >= 4:
            classification = parts[-2]
            client = parts[-4]  # Skip one level
            client_is_system = client.lower() in skip_dirs or client.lower() in skip_project_dirs

        # Only return if we found something that doesn't look like a system path
        if not (client_is_system and classification_is_system):
            return {
                'client': client if not client_is_system else None,
                'classification': classification if not classification_is_system else None
            }

    # Fallback: couldn't extract meaningful metadata
    return {
        'client': None,
        'classification': None
    }


class GraphitiManager:
    """Simplified manager for Graphiti operations."""

    def __init__(self, graphiti: Graphiti):
        """
        Initialize the Graphiti manager.

        Args:
            graphiti: Graphiti instance
        """
        self.graphiti = graphiti

    async def upload_file(self, file_path: str, show_progress: bool = True) -> Dict:
        """
        Upload a file as a single episode to Graphiti.

        Args:
            file_path: Path to the file to upload
            show_progress: Whether to print progress messages

        Returns:
            Dict with upload results including episode UUID, client, and classification
        """
        try:
            # Parse the file
            filename = Path(file_path).name
            if show_progress:
                print(f"  Parsing {filename}...")

            parsed = parse_file(file_path)
            word_count = len(parsed['content'].split())

            # Extract metadata from path (client + classification)
            metadata = extract_metadata_from_path(file_path)
            client = metadata['client']
            classification = metadata['classification']

            # Build source description with classification context
            if classification:
                source_desc = f"Classification: {classification} | Document: {filename}"
            else:
                source_desc = f"Document: {filename}"

            # Use client as group_id for multi-tenant isolation
            group_id = client if client else ""

            logger.info(
                f"Uploading file: {filename} ({word_count} words) "
                f"[Client: {client or 'N/A'}, Classification: {classification or 'N/A'}]"
            )

            if show_progress:
                if client and classification:
                    print(f"  Client: {client}, Classification: {classification}")
                print(f"  Extracting entities from {word_count} words...")

            # Create ONE episode for the entire file
            result = await self.graphiti.add_episode(
                name=filename,
                episode_body=parsed['content'],
                source=EpisodeType.text,
                source_description=source_desc,
                reference_time=datetime.now(timezone.utc),
                group_id=group_id,
                entity_types=entity_types,
            )

            logger.info(f"File uploaded successfully. Episode UUID: {result.episode.uuid}")

            if show_progress:
                print(f"  ✓ Created episode: {result.episode.uuid[:8]}...")

            return {
                'success': True,
                'filename': filename,
                'episode_uuid': result.episode.uuid,
                'word_count': word_count,
                'client': client,
                'classification': classification,
            }

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise

    async def upload_directory(self, directory_path: str, delay_seconds: float = 0) -> List[Dict]:
        """
        Upload all supported files in a directory.

        Args:
            directory_path: Path to the directory
            delay_seconds: Optional delay between file uploads (helps avoid rate limits)

        Returns:
            List of upload results
        """
        results = []
        directory = Path(directory_path)

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")

        # Supported file extensions
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.xlsx'}

        # Find all supported files
        files = [
            f for f in directory.rglob('*')
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]

        total_files = len(files)
        logger.info(f"Found {total_files} supported files in {directory_path}")

        # Upload each file with progress reporting
        for idx, file_path in enumerate(files, 1):
            try:
                # Progress header
                print(f"\n[{idx}/{total_files}] Processing: {file_path.name}")

                # Upload the file (with progress reporting)
                result = await self.upload_file(str(file_path), show_progress=True)
                results.append(result)

                # Optional delay between files (except after the last file)
                if delay_seconds > 0 and idx < total_files:
                    print(f"  Waiting {delay_seconds}s before next file to avoid rate limits...")
                    await asyncio.sleep(delay_seconds)

            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
                print(f"  ✗ Error: {str(e)}")
                results.append({
                    'success': False,
                    'filename': file_path.name,
                    'error': str(e)
                })

                # Still delay after failures to avoid rate limit cascades
                if delay_seconds > 0 and idx < total_files:
                    print(f"  Waiting {delay_seconds}s before next file...")
                    await asyncio.sleep(delay_seconds)

        return results

    async def search(self, query: str, num_results: int = 10) -> List:
        """
        Search the knowledge graph.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results (EntityEdge objects)
        """
        logger.info(f"Searching for: {query}")
        results = await self.graphiti.search(query, num_results=num_results)
        logger.info(f"Found {len(results)} results")
        return results

    async def clear_database(self):
        """Clear all data from the knowledge graph."""
        logger.warning("Clearing all data from the database")
        await clear_data(self.graphiti.driver)
        logger.info("Database cleared successfully")

    async def get_all_episodes(self) -> List:
        """
        Retrieve all episodic nodes from the graph.

        Returns:
            List of episodic nodes
        """
        from graphiti_core.nodes import EpisodicNode

        # Retrieve all episodes
        episodes = await self.graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=1000,  # Get up to 1000 episodes
        )

        return episodes

    async def deduplicate_entities(self, show_progress: bool = True) -> Dict:
        """
        Find and report duplicate entity nodes in the graph.

        This uses Graphiti's LLM-based deduplication to identify entities
        that refer to the same real-world object (e.g., "SHARIQ ALI" and "shariq").

        Args:
            show_progress: Whether to print progress messages

        Returns:
            Dict with deduplication results including duplicate groups found
        """
        try:
            if show_progress:
                print("Retrieving all entity nodes from the graph...")

            # Query all entity nodes using Neo4j directly
            async with self.graphiti.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (n:Entity)
                    RETURN n.uuid AS uuid, n.name AS name,
                           n.summary AS summary, labels(n) AS labels
                    """
                )
                records = await result.data()

            if not records:
                if show_progress:
                    print("No entity nodes found in the graph.")
                return {'duplicate_groups': [], 'total_entities': 0}

            total_entities = len(records)
            if show_progress:
                print(f"Found {total_entities} entities. Analyzing for duplicates...")

            # Group by name (case-insensitive) to find potential duplicates
            name_groups = {}
            for record in records:
                name_lower = record['name'].lower()
                if name_lower not in name_groups:
                    name_groups[name_lower] = []
                name_groups[name_lower].append(record)

            # Find groups with multiple entities (potential duplicates)
            duplicate_groups = [
                group for group in name_groups.values() if len(group) > 1
            ]

            if show_progress:
                print(f"\nFound {len(duplicate_groups)} potential duplicate groups:")
                for idx, group in enumerate(duplicate_groups, 1):
                    print(f"\nGroup {idx}:")
                    for entity in group:
                        print(f"  - {entity['name']} (UUID: {entity['uuid'][:8]}...)")

            return {
                'duplicate_groups': duplicate_groups,
                'total_entities': total_entities,
                'total_duplicate_groups': len(duplicate_groups),
            }

        except Exception as e:
            logger.error(f"Failed to deduplicate entities: {e}")
            raise

    def display_search_results(self, results: List):
        """
        Display search results in a readable format.

        Args:
            results: List of EntityEdge objects from search
        """
        if not results:
            print("\nNo results found.")
            return

        print(f"\n{'='*80}")
        print(f"Found {len(results)} results")
        print(f"{'='*80}\n")

        for idx, result in enumerate(results, 1):
            print(f"{idx}. {result.fact}")

            # Show temporal information if available
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f"   Valid from: {result.valid_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f"   Valid until: {result.invalid_at.strftime('%Y-%m-%d %H:%M:%S')}")

            print()

        print(f"{'='*80}\n")
