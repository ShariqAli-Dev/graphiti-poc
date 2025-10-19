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

logger = logging.getLogger(__name__)


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
            Dict with upload results including episode UUID
        """
        try:
            # Parse the file
            filename = Path(file_path).name
            if show_progress:
                print(f"  Parsing {filename}...")

            parsed = parse_file(file_path)
            word_count = len(parsed['content'].split())

            logger.info(f"Uploading file: {filename} ({word_count} words)")

            if show_progress:
                print(f"  Extracting entities from {word_count} words...")

            # Create ONE episode for the entire file
            result = await self.graphiti.add_episode(
                name=filename,
                episode_body=parsed['content'],
                source=EpisodeType.text,
                source_description=f"Document: {filename}",
                reference_time=datetime.now(timezone.utc),
            )

            logger.info(f"File uploaded successfully. Episode UUID: {result.episode.uuid}")

            if show_progress:
                print(f"  ✓ Created episode: {result.episode.uuid[:8]}...")

            return {
                'success': True,
                'filename': filename,
                'episode_uuid': result.episode.uuid,
                'word_count': word_count,
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
