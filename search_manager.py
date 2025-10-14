"""
Search management for Graphiti.
Handles 3 types of searches: Basic Hybrid, Center Node, and Node Search.
"""

import json
from typing import List, Dict, Optional
from datetime import datetime

from graphiti_core import Graphiti
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_RRF,
    EDGE_HYBRID_SEARCH_RRF,
)


class SearchManager:
    """Manages different search methods for Graphiti."""

    def __init__(self, graphiti: Graphiti):
        """
        Initialize the search manager.

        Args:
            graphiti: Graphiti instance
        """
        self.graphiti = graphiti

    async def basic_hybrid_search(
        self,
        query: str,
        num_results: int = 10,
        group_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Perform basic hybrid search combining semantic similarity and BM25.

        Args:
            query: Search query
            num_results: Number of results to return
            group_ids: Optional list of file IDs to filter by

        Returns:
            List of search results with facts/relationships
        """
        print(f"\nPerforming Basic Hybrid Search...")
        print(f"Query: {query}")
        if group_ids:
            print(f"Filtering by files: {', '.join(group_ids)}")

        results = await self.graphiti.search(
            query=query,
            num_results=num_results,
            group_ids=group_ids,
        )

        return self._format_edge_results(results, "Basic Hybrid Search")

    async def center_node_search(
        self,
        query: str,
        center_node_uuid: str,
        num_results: int = 10,
        group_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Perform search reranked by graph distance from a center node.

        Args:
            query: Search query
            center_node_uuid: UUID of the center node
            num_results: Number of results to return
            group_ids: Optional list of file IDs to filter by

        Returns:
            List of search results reranked by proximity
        """
        print(f"\nPerforming Center Node Search...")
        print(f"Query: {query}")
        print(f"Center Node: {center_node_uuid}")
        if group_ids:
            print(f"Filtering by files: {', '.join(group_ids)}")

        results = await self.graphiti.search(
            query=query,
            center_node_uuid=center_node_uuid,
            num_results=num_results,
            group_ids=group_ids,
        )

        return self._format_edge_results(results, "Center Node Search")

    async def node_search(
        self,
        query: str,
        num_results: int = 10,
        group_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Perform node search to find entity nodes instead of relationships.

        Args:
            query: Search query
            num_results: Number of results to return
            group_ids: Optional list of file IDs to filter by

        Returns:
            List of node results
        """
        print(f"\nPerforming Node Search...")
        print(f"Query: {query}")
        if group_ids:
            print(f"Filtering by files: {', '.join(group_ids)}")

        # Use the _search method with NODE_HYBRID_SEARCH_RRF recipe
        config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        config.limit = num_results

        # Set group_ids in the config
        if group_ids:
            config.group_ids = group_ids

        search_results = await self.graphiti._search(
            query=query,
            config=config,
        )

        return self._format_node_results(search_results, "Node Search")

    def _format_edge_results(self, results, search_type: str) -> List[Dict]:
        """
        Format edge/relationship search results for display.

        Args:
            results: List of EntityEdge objects
            search_type: Type of search performed

        Returns:
            List of formatted result dictionaries
        """
        formatted = []

        for idx, result in enumerate(results):
            formatted_result = {
                'rank': idx + 1,
                'search_type': search_type,
                'result_type': 'relationship',
                'uuid': result.uuid,
                'fact': result.fact,
                'source_node_uuid': result.source_node_uuid,
                'target_node_uuid': result.target_node_uuid,
                'created_at': result.created_at.isoformat() if result.created_at else None,
                'valid_at': result.valid_at.isoformat() if result.valid_at else None,
                'invalid_at': result.invalid_at.isoformat() if result.invalid_at else None,
                'group_id': result.group_id,
            }

            # Extract classification from group_id if available
            if result.group_id:
                parts = result.group_id.split('/')
                if len(parts) > 0:
                    formatted_result['classification'] = parts[0]
                    formatted_result['source_file'] = result.group_id

            formatted.append(formatted_result)

        return formatted

    def _format_node_results(self, search_results, search_type: str) -> List[Dict]:
        """
        Format node search results for display.

        Args:
            search_results: SearchResults object with nodes
            search_type: Type of search performed

        Returns:
            List of formatted result dictionaries
        """
        formatted = []

        for idx, node in enumerate(search_results.nodes):
            formatted_result = {
                'rank': idx + 1,
                'search_type': search_type,
                'result_type': 'entity',
                'uuid': node.uuid,
                'name': node.name,
                'summary': node.summary,
                'labels': list(node.labels) if node.labels else [],
                'created_at': node.created_at.isoformat() if node.created_at else None,
                'group_id': node.group_id,
            }

            # Extract classification from group_id if available
            if node.group_id:
                parts = node.group_id.split('/')
                if len(parts) > 0:
                    formatted_result['classification'] = parts[0]
                    formatted_result['source_file'] = node.group_id

            # Add attributes if available
            if hasattr(node, 'attributes') and node.attributes:
                formatted_result['attributes'] = node.attributes

            formatted.append(formatted_result)

        return formatted

    def display_results(self, results: List[Dict]):
        """
        Display search results in a readable format.

        Args:
            results: List of formatted search results
        """
        if not results:
            print("\nNo results found.")
            return

        print(f"\n{'='*80}")
        print(f"Found {len(results)} results")
        print(f"{'='*80}\n")

        for result in results:
            print(f"\n{'-'*80}")
            print(f"Rank #{result['rank']} | Type: {result['result_type'].upper()}")
            print(f"{'-'*80}")

            if result['result_type'] == 'relationship':
                self._display_edge_result(result)
            else:
                self._display_node_result(result)

        print(f"\n{'='*80}\n")

    def _display_edge_result(self, result: Dict):
        """Display a relationship/edge result."""
        print(f"\nFACT: {result['fact']}")
        print(f"\nUUID: {result['uuid']}")
        print(f"Source Node: {result['source_node_uuid']}")
        print(f"Target Node: {result['target_node_uuid']}")

        if result.get('source_file'):
            print(f"\nSource File: {result['source_file']}")
        if result.get('classification'):
            print(f"Classification: {result['classification']}")

        if result.get('created_at'):
            print(f"\nCreated: {result['created_at']}")
        if result.get('valid_at'):
            print(f"Valid From: {result['valid_at']}")
        if result.get('invalid_at'):
            print(f"Valid Until: {result['invalid_at']}")

    def _display_node_result(self, result: Dict):
        """Display an entity/node result."""
        print(f"\nENTITY: {result['name']}")
        print(f"\nUUID: {result['uuid']}")

        if result.get('summary'):
            summary = result['summary']
            if len(summary) > 200:
                summary = summary[:200] + "..."
            print(f"\nSummary: {summary}")

        if result.get('labels'):
            print(f"\nLabels: {', '.join(result['labels'])}")

        if result.get('source_file'):
            print(f"\nSource File: {result['source_file']}")
        if result.get('classification'):
            print(f"Classification: {result['classification']}")

        if result.get('attributes'):
            print(f"\nAttributes:")
            for key, value in result['attributes'].items():
                print(f"  {key}: {value}")

        if result.get('created_at'):
            print(f"\nCreated: {result['created_at']}")

    async def get_node_for_search(self, entity_name: str) -> Optional[str]:
        """
        Find a node UUID by entity name for use in center node search.

        Args:
            entity_name: Name of the entity to search for

        Returns:
            Node UUID if found, None otherwise
        """
        # Perform a basic search to find the entity
        config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        config.limit = 5

        results = await self.graphiti._search(
            query=entity_name,
            config=config,
        )

        if results.nodes:
            # Return the first matching node
            node = results.nodes[0]
            print(f"Found entity: {node.name} (UUID: {node.uuid})")
            return node.uuid

        return None
