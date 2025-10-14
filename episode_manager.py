"""
Episode management for Graphiti.
Handles hierarchical episode creation (parent + sections).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

from file_parsers import parse_file


class EpisodeManager:
    """Manages hierarchical episode creation for files."""

    def __init__(self, graphiti: Graphiti):
        """
        Initialize the episode manager.

        Args:
            graphiti: Graphiti instance
        """
        self.graphiti = graphiti

    def extract_classification(self, file_path: str) -> str:
        """
        Extract TC### classification from file path.

        Args:
            file_path: Path to the file

        Returns:
            Classification (e.g., "TC103") or "UNCLASSIFIED"
        """
        path_parts = Path(file_path).parts

        for part in path_parts:
            if part.upper().startswith('TC') and len(part) >= 4:
                # Extract TC followed by digits
                if part[2:5].isdigit():
                    return part[:5].upper()

        return "UNCLASSIFIED"

    def create_file_id(self, file_path: str, classification: str) -> str:
        """
        Create a unique file ID.

        Args:
            file_path: Path to the file
            classification: TC### classification

        Returns:
            File ID in format "classification/filename"
        """
        filename = Path(file_path).name
        return f"{classification}/{filename}"

    def create_parent_metadata(self, file_path: str, classification: str,
                               word_count: int, token_count: int,
                               has_sections: bool) -> Dict:
        """
        Create metadata for parent episode.

        Args:
            file_path: Path to the file
            classification: TC### classification
            word_count: Number of words
            token_count: Number of tokens
            has_sections: Whether file has sections

        Returns:
            Metadata dictionary
        """
        path = Path(file_path)

        return {
            "episode_type": "parent",
            "classification": classification,
            "filename": path.name,
            "file_extension": path.suffix,
            "file_size_bytes": os.path.getsize(file_path),
            "word_count": word_count,
            "token_count": token_count,
            "has_sections": has_sections,
            "upload_date": datetime.now(timezone.utc).isoformat(),
        }

    def create_section_metadata(self, file_id: str, classification: str,
                                section_name: str, section_index: int,
                                parent_episode_uuid: str) -> Dict:
        """
        Create metadata for section episode.

        Args:
            file_id: File identifier
            classification: TC### classification
            section_name: Name of the section
            section_index: Index of this section
            parent_episode_uuid: UUID of parent episode

        Returns:
            Metadata dictionary
        """
        return {
            "episode_type": "section",
            "classification": classification,
            "parent_file": file_id,
            "section_name": section_name,
            "section_index": section_index,
            "parent_episode_uuid": parent_episode_uuid,
        }

    async def upload_file(self, file_path: str, version: str = None) -> Dict:
        """
        Upload a file to Graphiti with hierarchical episodes.

        Args:
            file_path: Path to the file
            version: Optional version identifier (e.g., "Q3_2024")

        Returns:
            Dictionary with upload results
        """
        # Parse the file
        print(f"Parsing file: {file_path}")
        parsed = parse_file(file_path)

        # Extract metadata
        classification = self.extract_classification(file_path)
        file_id = self.create_file_id(file_path, classification)

        if version:
            file_id = f"{file_id}@{version}"

        print(f"File ID: {file_id}")
        print(f"Classification: {classification}")
        print(f"Word count: {parsed['word_count']}")
        print(f"Token count: {parsed['token_count']}")
        print(f"Sections detected: {len(parsed['sections'])}")

        # Create parent episode
        parent_metadata = self.create_parent_metadata(
            file_path, classification,
            parsed['word_count'], parsed['token_count'],
            parsed['has_sections']
        )

        # Create file summary for parent episode
        filename = Path(file_path).name
        file_summary = f"""File: {filename}
Classification: {classification}
Type: {Path(file_path).suffix}
Word Count: {parsed['word_count']}
Token Count: {parsed['token_count']}
Sections: {len(parsed['sections'])}

Document structure overview:
{chr(10).join([f"- {name}" for name, _ in parsed['sections'][:10]])}
"""

        print(f"\nCreating parent episode...")
        parent_result = await self.graphiti.add_episode(
            name=f"PARENT:{file_id}",
            episode_body=file_summary,
            source=EpisodeType.json,
            source_description=json.dumps(parent_metadata),
            reference_time=datetime.now(timezone.utc),
            group_id=file_id,
        )

        parent_uuid = parent_result.episode_uuid
        print(f"Parent episode created: {parent_uuid}")

        # Create section episodes
        section_results = []
        sections_to_process = []

        if parsed['has_sections'] and parsed['sections']:
            # Use detected sections
            sections_to_process = parsed['sections']
        elif parsed['token_count'] < 5000:
            # Small file without sections - single content episode
            sections_to_process = [("Main Content", parsed['full_text'])]
        else:
            # Large file without clear sections - chunk it
            print("File is large and has no clear sections. Chunking...")
            parser = parsed['parser']
            chunks = parser.chunk_text(parsed['full_text'])
            sections_to_process = [(f"Chunk {i+1}", chunk) for i, chunk in enumerate(chunks)]

        print(f"\nCreating {len(sections_to_process)} section episodes...")

        for idx, (section_name, section_content) in enumerate(sections_to_process):
            section_metadata = self.create_section_metadata(
                file_id, classification, section_name, idx, parent_uuid
            )

            result = await self.graphiti.add_episode(
                name=f"SECTION:{section_name}",
                episode_body=section_content,
                source=EpisodeType.text,
                source_description=json.dumps(section_metadata),
                reference_time=datetime.now(timezone.utc),
                group_id=file_id,
                previous_episode_uuids=[parent_uuid] if idx == 0 else [section_results[-1]['episode_uuid']],
            )

            section_results.append({
                'episode_uuid': result.episode_uuid,
                'section_name': section_name,
                'section_index': idx,
            })

            print(f"  Section {idx+1}/{len(sections_to_process)}: {section_name}")

        print(f"\nFile upload complete!")
        print(f"  Parent episode: {parent_uuid}")
        print(f"  Section episodes: {len(section_results)}")

        return {
            'file_id': file_id,
            'classification': classification,
            'parent_uuid': parent_uuid,
            'section_uuids': [s['episode_uuid'] for s in section_results],
            'total_episodes': 1 + len(section_results),
        }

    async def delete_file(self, file_id: str) -> Dict:
        """
        Delete all episodes for a given file.

        Args:
            file_id: File identifier to delete

        Returns:
            Dictionary with deletion results
        """
        print(f"Retrieving episodes for file: {file_id}")

        # Retrieve all episodes for this file
        episodes = await self.graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=1000,  # Retrieve many episodes
            group_ids=[file_id],
        )

        if not episodes:
            print(f"No episodes found for file ID: {file_id}")
            return {
                'file_id': file_id,
                'deleted_count': 0,
            }

        print(f"Found {len(episodes)} episodes to delete")

        deleted_count = 0
        for episode in episodes:
            await self.graphiti.remove_episode(episode.uuid)
            deleted_count += 1
            print(f"  Deleted episode: {episode.uuid}")

        print(f"\nDeleted {deleted_count} episodes for file: {file_id}")

        return {
            'file_id': file_id,
            'deleted_count': deleted_count,
        }

    async def list_files(self) -> List[Dict]:
        """
        List all files in the knowledge graph.

        Returns:
            List of file information dictionaries
        """
        # Retrieve all recent episodes
        episodes = await self.graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=10000,  # Get many episodes
        )

        # Group by file_id (group_id in Graphiti)
        files = {}

        for episode in episodes:
            group_id = episode.group_id

            if not group_id:
                continue

            if group_id not in files:
                files[group_id] = {
                    'file_id': group_id,
                    'episode_count': 0,
                    'parent_uuid': None,
                    'classification': None,
                }

            files[group_id]['episode_count'] += 1

            # Parse metadata if available
            if episode.source_description:
                try:
                    metadata = json.loads(episode.source_description)
                    if metadata.get('episode_type') == 'parent':
                        files[group_id]['parent_uuid'] = episode.uuid
                        files[group_id]['classification'] = metadata.get('classification')
                        files[group_id]['upload_date'] = metadata.get('upload_date')
                        files[group_id]['word_count'] = metadata.get('word_count')
                        files[group_id]['has_sections'] = metadata.get('has_sections')
                except json.JSONDecodeError:
                    pass

        return list(files.values())

    async def get_file_details(self, file_id: str) -> Dict:
        """
        Get detailed information about a specific file.

        Args:
            file_id: File identifier

        Returns:
            Dictionary with file details
        """
        episodes = await self.graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=1000,
            group_ids=[file_id],
        )

        if not episodes:
            return None

        parent_info = None
        sections = []

        for episode in episodes:
            if episode.source_description:
                try:
                    metadata = json.loads(episode.source_description)

                    if metadata.get('episode_type') == 'parent':
                        parent_info = {
                            'uuid': episode.uuid,
                            'metadata': metadata,
                            'name': episode.name,
                        }
                    elif metadata.get('episode_type') == 'section':
                        sections.append({
                            'uuid': episode.uuid,
                            'section_name': metadata.get('section_name'),
                            'section_index': metadata.get('section_index'),
                        })
                except json.JSONDecodeError:
                    pass

        return {
            'file_id': file_id,
            'parent': parent_info,
            'sections': sorted(sections, key=lambda s: s.get('section_index', 0)),
            'total_episodes': len(episodes),
        }
