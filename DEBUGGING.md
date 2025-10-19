# Debugging Guide

## Logging Added

Comprehensive logging has been added to help debug issues with the Graphiti CLI.

### Log Levels

The CLI now logs at multiple levels:
- **DEBUG**: Detailed information about every step
- **INFO**: Important milestones (function calls, successful operations)
- **ERROR**: Errors with full stack traces

### Where Logs Appear

All logs are printed to the console (stdout/stderr) with timestamps. You'll see them mixed with the regular output.

### Log Format

```
YYYY-MM-DD HH:MM:SS - module_name - LEVEL - message
```

Example:
```
2025-10-14 17:30:15 - __main__ - INFO - === UPLOAD FILE FUNCTION CALLED ===
2025-10-14 17:30:15 - episode_manager - DEBUG - Calling parse_file()
2025-10-14 17:30:16 - episode_manager - INFO - File parsed successfully: 1234 words, 1500 tokens
```

### Key Log Messages to Watch For

**When uploading a file:**
1. `=== UPLOAD FILE FUNCTION CALLED ===` - CLI upload method started
2. `=== STARTING UPLOAD_FILE ===` - EpisodeManager upload started
3. `Calling parse_file()` - File parsing begins
4. `Calling graphiti.add_episode() for parent` - Creating parent episode
5. `Parent episode UUID: <uuid>` - Parent episode created successfully
6. `Calling graphiti.add_episode() for section <name>` - Creating each section
7. `Upload complete: X total episodes` - Upload finished

**When listing files:**
1. `=== LIST FILES FUNCTION CALLED ===` - CLI list method started
2. `=== STARTING LIST_FILES ===` - EpisodeManager list started
3. `Calling graphiti.retrieve_episodes()` - Fetching episodes from Graphiti
4. `Retrieved X episodes from Graphiti` - Episodes retrieved
5. `Found X unique files` - Files grouped

**When deleting files:**
1. `=== DELETE FILE FUNCTION CALLED ===` - CLI delete method started
2. `Deleting file: <file_id>` - Deletion started
3. `Deleted X episodes` - Deletion complete

### Common Issues to Look For

**Issue 1: Function Not Being Called**
If you don't see `=== UPLOAD FILE FUNCTION CALLED ===` when you select option 1, the CLI menu is not routing correctly.

**Issue 2: Graphiti Connection Failed**
Look for errors during initialization:
```
ERROR - Failed to initialize Graphiti: <error message>
```

**Issue 3: Parse Errors**
If file parsing fails:
```
ERROR - Upload failed with exception: <error>
```

**Issue 4: Episode Creation Failed**
If `add_episode()` fails, you'll see:
```
ERROR - Upload failed with exception: <error>
```
Followed by a full stack trace.

**Issue 5: No Episodes Retrieved**
If list_files returns 0 episodes:
```
INFO - Retrieved 0 episodes from Graphiti
```
This means either:
- Nothing has been uploaded yet
- Neo4j connection is working but database is empty
- Graphiti indices aren't built correctly

### Redirecting Logs to a File

To save logs to a file for later analysis:

```bash
python3 cli.py 2>&1 | tee graphiti_debug.log
```

This will show logs on screen AND save them to `graphiti_debug.log`.

### Reducing Log Noise

If the DEBUG logs are too noisy, you can edit `cli.py` and change:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change to logging.INFO or logging.ERROR
    ...
)
```

## Next Steps

1. Run the CLI: `python3 cli.py`
2. Watch the logs carefully during upload/list/delete operations
3. If you see an error, look at the full stack trace
4. Share the relevant log section if you need help debugging

The logs will tell us exactly where the process is failing!
