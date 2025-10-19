# Graphiti Document Manager - Simplified

A clean, production-ready CLI for managing documents in a Graphiti knowledge graph. Built on the graphiti-agent reference implementation.

## What Changed?

**Old Version (Complex):**
- ~1500 lines of over-engineered code
- Complex parent/child episode hierarchies
- Custom file tracking systems
- Heavy metadata management
- Custom search wrappers
- Hard to debug and maintain

**New Version (Simplified):**
- ~500 lines of clean, focused code
- One episode per file (simple!)
- Direct Graphiti API usage
- Pydantic AI agent for natural language Q&A
- Easy to understand and extend

## Architecture

```
graphiti/
├── .env                      # Your credentials (PRESERVED)
├── cli.py                    # Simple menu-driven CLI
├── graphiti_manager.py       # Episode management (50 lines)
├── agent.py                  # Pydantic AI Q&A agent
├── file_parsers.py           # Simple text extraction
├── requirements.txt          # Core dependencies
└── _old_implementation/      # Archived old code
```

## Quick Start

### 1. Prerequisites

- **Neo4j** (running locally or remotely)
- **Python 3.10+**
- **OpenAI API key**

### 2. Start Neo4j

```bash
# Using Docker
docker start neo4j

# OR using Neo4j Desktop
# Start your database via the GUI
```

### 3. Configure Environment

Your `.env` file should already be configured (it was preserved during the refactor):

```env
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# OpenAI API
OPENAI_API_KEY=your_openai_key
MODEL_CHOICE=gpt-4o-mini

# Rate Limiting Control
# Lower = slower but avoids rate limits
# Higher = faster but may hit rate limits
# Recommended: 3-5 for free tier, 10-20 for paid tier
SEMAPHORE_LIMIT=5
```

### 4. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

### 5. Run the CLI

```bash
python3 cli.py
```

## Features

### 1. Upload File
- Upload a single file to the knowledge graph
- One episode per file (simple!)
- Supported formats: PDF, DOCX, TXT, MD, XLSX

### 2. Upload Directory
- Batch upload all supported files in a directory
- Recursive scanning
- Progress reporting

### 3. Search Graph (Raw Facts)
- Direct hybrid search (semantic + BM25)
- Returns raw facts from the knowledge graph
- Fast and straightforward

### 4. Ask Question (AI Agent)
- Natural language Q&A over your documents
- Powered by Pydantic AI
- Streaming responses with rich markdown formatting
- Maintains conversation history

### 5. List All Episodes
- View all documents in the knowledge graph
- See UUIDs, creation dates, content previews

### 6. Reset Database
- Clear all data from Neo4j
- Requires confirmation
- Fresh start for testing

## How It Works

### Episode Creation (Simplified)

**Old way (complex):**
```python
# Parent episode
parent = await graphiti.add_episode(...)

# Then 10 section episodes linked to parent
for section in sections:
    await graphiti.add_episode(...link to parent...)
```

**New way (simple):**
```python
# ONE episode per file - that's it!
await graphiti.add_episode(
    name=filename,
    episode_body=file_content,
    source=EpisodeType.text,
    source_description=f"Document: {filename}",
    reference_time=datetime.now(timezone.utc),
)
```

Graphiti automatically handles:
- ✅ Entity extraction
- ✅ Relationship building
- ✅ Deduplication across files
- ✅ Temporal tracking

### Search (Direct API)

**Old way:**
```python
search_manager = SearchManager(graphiti)
results = await search_manager.basic_hybrid_search(...)
formatted = self._format_edge_results(...)
self.display_results(formatted)
```

**New way:**
```python
# Direct Graphiti call
results = await graphiti.search(query)
for result in results:
    print(f"Fact: {result.fact}")
```

### Q&A Agent (Pydantic AI)

The AI agent provides natural language answers by:
1. Searching the knowledge graph for relevant facts
2. Synthesizing facts into coherent answers
3. Streaming responses with rich formatting
4. Maintaining conversation context

Example interaction:
```
[You] What is the Alpha Project?

[Assistant] The Alpha Project is a development initiative being undertaken
by TechCorp. It involves John Smith and Mary Johnson, who are using Python
and React technologies. The project focuses on artificial intelligence
concepts and is located in San Francisco.
```

## File Structure

### Core Files

**cli.py** (~300 lines)
- Menu-driven interface
- Async/await throughout
- Clean error handling

**graphiti_manager.py** (~150 lines)
- Simple upload/search/delete operations
- Direct Graphiti API usage
- No complex wrappers

**agent.py** (~250 lines)
- Pydantic AI agent setup
- Search tool for knowledge graph
- Streaming responses with Rich

**file_parsers.py** (~150 lines)
- Simple text extraction
- No chunking or section detection
- Supports: PDF, DOCX, TXT, MD, XLSX

## New Features

### Tab Completion for File Paths

The CLI now supports **tab completion** when entering file or directory paths:

```bash
# Type partial path and press TAB
Enter file path: inputs/fou<TAB>
# Autocompletes to: inputs/founders-contracts/

# Press TAB again to see all matches
Enter file path: inputs/<TAB><TAB>
# Shows: inputs/file1.pdf  inputs/file2.txt  inputs/founders-contracts/
```

Works for:
- Absolute paths: `/home/user/documents/`
- Relative paths: `./inputs/`
- Home directory: `~/Documents/`

### Rate Limiting Control

Control API request concurrency via `SEMAPHORE_LIMIT` in `.env`:

```env
# Conservative (free tier) - slower but safe
SEMAPHORE_LIMIT=3

# Balanced (low paid tier) - good speed, low risk
SEMAPHORE_LIMIT=5

# Aggressive (high paid tier) - fast, may hit limits
SEMAPHORE_LIMIT=20
```

**See [RATE_LIMITING.md](RATE_LIMITING.md) for detailed guide.**

## Troubleshooting

### Neo4j Connection Error

```
ConnectionRefusedError: Connect call failed ('127.0.0.1', 7687)
```

**Solution:** Start your Neo4j database first.

### Import Error: pydantic-ai

```
ModuleNotFoundError: No module named 'pydantic_ai'
```

**Solution:**
```bash
pip install pydantic-ai==0.2.9 pydantic-ai-slim==0.2.9 rich==14.0.0
```

### Agent Doesn't Find Information

**Solution:** Make sure you've uploaded documents first (Option 1 or 2).

## Comparing to Reference Implementation

This project is based on the [graphiti-agent](./graphiti-agent/) reference implementation, which demonstrates best practices for using Graphiti.

**What we kept:**
- ✅ Simple episode creation pattern
- ✅ Direct Graphiti API usage
- ✅ Pydantic AI for Q&A
- ✅ Clean async patterns

**What we added:**
- ✅ File upload capabilities (PDF, DOCX, etc.)
- ✅ Directory batch upload
- ✅ Interactive CLI menu
- ✅ Episode listing and management

## Next Steps

### To Add More File Types

Edit `file_parsers.py`:

```python
def parse_your_format(file_path: str) -> str:
    # Your parsing logic
    return extracted_text

# Then add to parse_file():
elif extension == '.yourext':
    content = parse_your_format(file_path)
```

### To Customize the Agent

Edit `agent.py`:

```python
graphiti_agent = Agent(
    get_model(),
    system_prompt="""Your custom instructions here...""",
    deps_type=GraphitiDependencies
)
```

### To Add Custom Entity Types

Create `entity_types.py`:

```python
from pydantic import BaseModel

class Person(BaseModel):
    """An individual human being."""
    pass

entity_types = {"Person": Person, ...}
```

Then pass to `add_episode()`:
```python
await graphiti.add_episode(
    ...,
    entity_types=entity_types,
)
```

## Resources

- [Graphiti Documentation](https://help.getzep.com/graphiti)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Neo4j Documentation](https://neo4j.com/docs/)

## Old Implementation

The previous complex implementation is archived in `_old_implementation/` for reference.

## License

Based on code from Zep Software, Inc. under the Apache License 2.0.
