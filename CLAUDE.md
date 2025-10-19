# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project is a comprehensive CLI tool for managing documents in a Graphiti knowledge graph. It uses Neo4j for graph storage and OpenAI for LLM-powered entity extraction and semantic search. The tool supports hierarchical document processing, multiple search methods, and file management operations.

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

## CLI Features

The CLI provides 8 main commands:

1. **Upload File(s)**: Upload single files or entire directories with automatic parsing
2. **Delete File**: Remove all episodes for a specific file
3. **List All Files**: View all files grouped by classification
4. **Show File Details**: View episodes and sections for a specific file
5. **Refresh File**: Delete and re-upload a file (for updates)
6. **Search Knowledge Graph**: Query using 3 different search methods
7. **Reset Database**: Delete all nodes/relationships (keeps indices)
8. **Cleanup Orphaned Entities**: Remove entities only referenced by deleted episodes

## Code Architecture

### Module Structure

The codebase is organized into specialized modules:

1. **cli.py** - Main interactive CLI interface
   - `GraphitiCLI` class: Manages the interactive menu and user commands
   - Async main loop for handling user input
   - Integration point for all other modules

2. **file_parsers.py** - Document parsing for multiple formats
   - Supports: PDF, DOCX, TXT, MD, XLSX
   - `FileParser` base class with chunking and section detection
   - Specialized parsers: `PDFParser`, `DOCXParser`, `ExcelParser`, `TextParser`
   - Token counting using tiktoken (GPT-4 encoding)

3. **episode_manager.py** - Hierarchical episode creation
   - `EpisodeManager` class: Manages file uploads and deletions
   - Creates parent episodes (file metadata) + section episodes (content)
   - Tracks files using `group_id` parameter
   - Extracts TC### classifications from file paths

4. **search_manager.py** - Three search methods
   - `SearchManager` class: Handles all search operations
   - Basic Hybrid Search: Semantic + BM25 keyword search
   - Center Node Search: Reranks by graph distance from an entity
   - Node Search: Returns entity nodes instead of relationships

### Hierarchical Episode Structure

Every uploaded file creates a two-tier episode hierarchy:

**Parent Episode** (always created):
- Stores file metadata (filename, classification, word count, token count)
- Episode type: "parent"
- Uses `group_id` to identify the file (format: "TC103/filename.pdf")
- Metadata stored in `source_description` as JSON

**Section Episodes** (created based on document structure):
- Documents with detected headers: One episode per section
- Small files (<5000 tokens): Single content episode
- Large files without structure: Chunked semantically (~1500 tokens, 200 token overlap)
- Excel files: One episode per sheet
- Linked to parent via `previous_episode_uuids`

### File Tracking System

**Client-Level Entity Linking (Multi-Tenant Architecture)**:
- Uses **client_id** as `group_id` for entity namespace isolation
- All files for a client share the same `group_id` → entities automatically link across documents
- Different clients have different `group_id` → complete isolation
- Example: `/inputs/` directory → all files get `group_id: "client-inputs"`

**Individual File Tracking**:
- **file_id** stored in episode metadata for individual file management
- Format: `"classification-filename"` (e.g., `"TC103-Q3_Report_pdf"`)
- With version: `"TC103-Q3_Report_pdf-v-Q3_2024"`
- Used for file deletion, listing, and detail queries

**How It Works**:
```python
# Three founder contract PDFs in /inputs/founders contracts/:
# - Shariq_Ali_FOUNDER_AGREEMENTS.pdf
# - Eliot_Puplett_FOUNDER_AGREEMENTS.pdf
# - Aamina_Bawany_FOUNDER_AGREEMENTS.pdf

# All get: group_id = "client-inputs"
# Individual file_ids in metadata:
#   - "TC103-Shariq_Ali_FOUNDER_AGREEMENTS_pdf"
#   - "TC103-Eliot_Puplett_FOUNDER_AGREEMENTS_pdf"
#   - "TC103-Aamina_Bawany_FOUNDER_AGREEMENTS_pdf"

# Result: Graphiti's LLM automatically merges duplicate entities
# "CompanyX" mentioned in all 3 files → single entity node
```

### Search Methods

**1. Basic Hybrid Search** (search_manager.py:14-39)
- Combines semantic similarity (embeddings) and BM25 (keyword matching)
- Uses Reciprocal Rank Fusion (RRF) to merge results
- Returns relationship edges (facts) between entities
- Default method for most queries

**2. Center Node Search** (search_manager.py:41-70)
- First performs hybrid search
- Reranks results by graph distance from a specified entity
- Useful for exploring relationships around specific entities
- Example: "Show everything related to Project Alpha"

**3. Node Search** (search_manager.py:72-99)
- Uses `NODE_HYBRID_SEARCH_RRF` recipe
- Returns entity nodes instead of relationships
- Includes node name, summary, labels, and attributes
- Best for finding entities rather than facts

### File Upload Process (episode_manager.py:218-380)

1. Parse file using appropriate parser
2. Extract TC### classification from file path
3. Create **file_id** for tracking: `"{classification}-{filename}"` (sanitized)
4. Extract **client_id** from base directory for `group_id` namespace
5. Create parent episode with file metadata (includes file_id)
6. Detect sections or chunk content based on size/structure:
   - Sections detected → One episode per section
   - <5000 tokens, no sections → Single content episode
   - >5000 tokens, no sections → Semantic chunking
7. Create section episodes linked to parent
8. All episodes use **client_id as group_id** for entity linking
9. Return upload results with file_id, client_id, and UUIDs

### File Deletion (episode_manager.py:387-440)

1. Retrieve all episodes (cannot filter by group_id since shared across files)
2. Filter episodes by **file_id** in metadata
3. Delete each matching episode using `remove_episode(uuid)`
4. Entities remain in graph (may be referenced by other files)
5. Use "Cleanup Orphaned Entities" command to remove unreferenced entities

### Database Operations

**Reset Database** (cli.py:466-488):
- Deletes all nodes and relationships
- Preserves indices and constraints (Option A strategy)
- Requires typing 'DELETE EVERYTHING' to confirm
- Uses `clear_data()` from graphiti utils

**Cleanup Orphaned Entities** (cli.py:490-543):
- Finds entities not referenced by any episodic nodes
- Uses Cypher query to identify orphans
- Optional deletion after review

## Development Notes

### Async Patterns
- All Graphiti operations are async
- Use `await` for all graphiti, episode_manager, and search_manager calls
- Main entry point uses `asyncio.run(main())`

### File Classification
- TC### classifications are auto-extracted from file paths
- Format: TC followed by 3 digits (e.g., TC103, TC104)
- Falls back to "UNCLASSIFIED" if no match found
- Used for organizing and filtering files

### Client ID Extraction (episode_manager.py:83-135)
- Automatically extracts client_id from file path for multi-tenant isolation
- Skips common system/project directories: `/home`, `/usr`, `/projects`, `/sandbox`, `/graphiti`
- Uses first meaningful directory as client identifier
- Examples:
  - `/home/user/projects/graphiti/inputs/file.pdf` → `"client-inputs"`
  - `/data/client-abc/documents/file.pdf` → `"client-client-abc"`
- Sanitized to meet Graphiti's group_id requirements (alphanumeric, dashes, underscores only)

### Metadata Storage
- Parent metadata: JSON in `source_description` field (includes `file_id`, `classification`, `filename`, etc.)
- Section metadata: Links to parent via `parent_episode_uuid` and stores `parent_file` (file_id)
- Episode type tracked via `episode_type` field: "parent" or "section"
- **file_id** used for individual file operations (deletion, details)
- **group_id** (client_id) used for entity linking across files

### Token Limits
- Uses tiktoken with cl100k_base encoding (GPT-4)
- Default chunk size: 1500 tokens
- Chunk overlap: 200 tokens
- Files must fit within LLM context window for processing

### Error Handling
- File parsers raise `ValueError` for unsupported file types
- Missing files raise `FileNotFoundError`
- All CLI commands have try/except blocks with user-friendly error messages

## File Reference Examples

- **File parsing**: file_parsers.py:205-234 (`parse_file` function)
- **Episode creation**: episode_manager.py:89-177 (`upload_file` method)
- **Search display**: search_manager.py:141-202 (`display_results` method)
- **CLI menu**: cli.py:47-62 (`display_menu` method)
