# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project is a simplified CLI tool for managing documents in a Graphiti knowledge graph. It uses Neo4j for graph storage and OpenAI for LLM-powered entity extraction and semantic search. The tool supports document upload, AI-powered Q&A, and knowledge graph search.

## Architecture

### Core Principle: Simplicity

This codebase follows the **one episode per file** pattern - no complex hierarchies, no custom file tracking systems. We let Graphiti handle entity extraction, deduplication, and relationship building automatically.

### Module Structure

1. **cli.py** (~390 lines) - Main interactive CLI interface
   - `GraphitiCLI` class: Manages the interactive menu and user commands
   - Tab completion for file paths
   - Async main loop for handling user input
   - 8 commands: Upload File, Upload Directory, Search Graph, Ask Question, List Episodes, Deduplicate Entities, Reset Database, Exit

2. **graphiti_manager.py** (~350 lines) - Document upload and search operations
   - `GraphitiManager` class: Manages file uploads, directory uploads, search, and database operations
   - `extract_metadata_from_path()`: Extracts client and classification from file paths (best-effort)
   - Direct Graphiti API usage - no unnecessary wrappers
   - One episode per file - simple and clean

3. **agent.py** (~240 lines) - Pydantic AI agent for natural language Q&A
   - `graphiti_agent`: Pydantic AI agent with search tool
   - `search_graphiti()`: Tool function for searching the knowledge graph
   - `run_interactive_agent()`: Interactive Q&A loop with streaming responses
   - Uses Rich for markdown formatting

4. **file_parsers.py** (~200 lines) - Document parsing for multiple formats
   - Supports: PDF, DOCX, TXT, MD, XLSX
   - `parse_file()`: Main entry point that delegates to format-specific parsers
   - Comprehensive error handling for encrypted PDFs, corrupted files, encoding issues
   - No chunking or section detection - just extract raw text

5. **entity_types.py** (~176 lines) - Entity type definitions for Graphiti
   - Defines 10 entity types: Person, Organization, Project, Location, LegalTerm, FinancialMetric, Technology, Event, Document, Concept
   - Uses Pydantic BaseModel for documentation purposes
   - Passed to `graphiti.add_episode()` to guide entity extraction

## Environment Setup

### Prerequisites
- Neo4j database (running locally at `neo4j://127.0.0.1:7687` or remotely)
- Python 3.10+
- OpenAI API key

### Configuration
Environment variables in `.env`:
- `NEO4J_URI`: Neo4j connection URI
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password
- `OPENAI_API_KEY`: OpenAI API key for LLM operations
- `MODEL_CHOICE`: OpenAI model to use (default: `gpt-4o-mini`)
- `SEMAPHORE_LIMIT`: Concurrent API calls during entity extraction (default: 5)
- `UPLOAD_DELAY_SECONDS`: Delay between file uploads in batch mode (default: 1)

### Setup Commands
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the CLI
python3 cli.py
```

## How It Works

### Simple Episode Creation

Every uploaded file creates **one episode**:

```python
await graphiti.add_episode(
    name=filename,
    episode_body=file_content,
    source=EpisodeType.text,
    source_description=f"Classification: {classification} | Document: {filename}",
    reference_time=datetime.now(timezone.utc),
    group_id=client,  # For multi-tenant isolation
    entity_types=entity_types,  # Guide entity extraction
)
```

Graphiti automatically:
- Extracts entities (Person, Organization, etc.)
- Creates relationships between entities
- Deduplicates entities across files
- Tracks temporal validity of facts

### Multi-Tenant Isolation

Files are grouped by **client** using the `group_id` parameter:
- Same client → same `group_id` → entities automatically link across documents
- Different clients → different `group_id` → complete isolation
- Client is extracted from file path using `extract_metadata_from_path()`

Example:
```
/inputs/tener/TC103/Q1_Report.pdf
          ↓
client = "tener"
classification = "TC103"
group_id = "tener"
```

### Search Methods

1. **Basic Search** (`graphiti.search(query)`)
   - Hybrid search: semantic similarity + BM25 keyword matching
   - Returns relationship edges (facts) between entities
   - Default method for most queries

2. **AI Agent Q&A** (`agent.py`)
   - Natural language questions
   - Searches graph and synthesizes answers
   - Streaming responses with conversation history

### File Upload Process

1. Parse file using appropriate parser
2. Extract metadata from file path (client, classification)
3. Create one episode for the entire file
4. Graphiti extracts entities and relationships automatically
5. Return upload results with episode UUID

### Database Operations

**Reset Database**:
- Deletes all nodes and relationships
- Preserves indices and constraints
- Requires typing 'DELETE EVERYTHING' to confirm

**Deduplicate Entities**:
- Finds entities with similar names (case-insensitive)
- Reports potential duplicates for review
- Does not automatically merge (safe operation)

## Development Notes

### Async Patterns
- All Graphiti operations are async
- Use `await` for all graphiti, manager, and agent calls
- Main entry point uses `asyncio.run(main())`

### Error Handling
- All file parsers have comprehensive error handling
- Validation happens early (fail fast)
- Clear error messages for common issues:
  - Missing environment variables
  - Encrypted/corrupted files
  - Encoding errors
  - Password-protected documents

### Path Metadata Extraction
- Best-effort extraction from file paths
- Skips system directories (home, usr, var, etc.)
- Skips project structure directories (projects, sandbox, graphiti)
- Returns `None` for ambiguous paths
- For ambiguous cases, you may need manual metadata specification

### Rate Limiting
- `SEMAPHORE_LIMIT`: Controls concurrent API calls within each file upload
- `UPLOAD_DELAY_SECONDS`: Delay between files in batch uploads
- See RATE_LIMITING.md for detailed tuning guide
- Conservative defaults prevent rate limit errors

## File Reference Examples

- **CLI menu**: cli.py:125-138
- **File upload**: graphiti_manager.py:84-155
- **Path metadata extraction**: graphiti_manager.py:29-89
- **PDF parsing with error handling**: file_parsers.py:22-68
- **AI agent search tool**: agent.py:71-109
- **Entity type definitions**: entity_types.py:15-164

## Common Tasks

### Add a New File Format

1. Add parser function to `file_parsers.py`:
   ```python
   def parse_your_format(file_path: str) -> str:
       try:
           # Your parsing logic
           return extracted_text
       except Exception as e:
           raise ValueError(f"Failed to parse: {e}")
   ```

2. Add to `parse_file()` function:
   ```python
   elif extension == '.yourext':
       content = parse_your_format(file_path)
   ```

3. Update `supported_extensions` in `graphiti_manager.py:175`

### Add New Entity Types

Edit `entity_types.py`:
```python
class YourEntity(BaseModel):
    """Description of your entity type."""
    pass

entity_types = {
    ...
    "YourEntity": YourEntity,
}
```

### Customize AI Agent Behavior

Edit `agent.py:47-56`:
```python
graphiti_agent = Agent(
    get_model(),
    system_prompt="""Your custom instructions here...""",
    deps_type=GraphitiDependencies
)
```

## Resources

- Graphiti documentation: https://help.getzep.com/graphiti
- Pydantic AI documentation: https://ai.pydantic.dev/
- Neo4j documentation: https://neo4j.com/docs/

## Important Notes

This is a **simplified** implementation that prioritizes clarity and maintainability over features. If you need more complex functionality:
- Custom file tracking systems
- Hierarchical episode structures
- Advanced search methods
- Custom entity deduplication

Consider whether Graphiti's built-in capabilities can handle your use case before adding complexity.
