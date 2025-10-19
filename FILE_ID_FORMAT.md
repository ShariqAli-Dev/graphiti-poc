# File ID Format

## Graphiti group_id Validation Rules

Graphiti requires `group_id` to contain **only**:
- Alphanumeric characters (A-Z, a-z, 0-9)
- Dashes (-)
- Underscores (_)

## Our File ID Sanitization

Since file paths naturally contain slashes (`/`) and periods (`.`), we sanitize them:

### Conversion Rules

| Character | Replacement | Reason |
|-----------|-------------|--------|
| `/` | `-` | Slash becomes dash (classification separator) |
| `.` | `_` | Period becomes underscore (file extension) |
| `@` | `-v-` | At symbol becomes `-v-` (version separator) |
| Other special chars | Removed | Any remaining invalid characters stripped |

### Examples

**Original path → Sanitized file_id:**

```
inputs/TC103/Q1_2024_Report.txt → TC103-Q1_2024_Report_txt

inputs/TC104/Financial_Summary.pdf → TC104-Financial_Summary_pdf

TC103/Q3_Report.xlsx@Q3_2024 → TC103-Q3_Report_xlsx-v-Q3_2024
```

## How This Affects You

### When Uploading Files

The CLI will automatically convert file paths to valid `file_id` format:

```bash
# You upload: inputs/TC103/Q1_2024_Report.txt
# Stored as:  TC103-Q1_2024_Report_txt
```

### When Deleting Files

Use the sanitized format when specifying file IDs:

```bash
# To delete:  inputs/TC103/Q1_2024_Report.txt
# Use:        TC103-Q1_2024_Report_txt
```

### When Listing Files

The "List All Files" command will show file IDs in sanitized format:

```
TC103:
  File ID: TC103-Q1_2024_Report_txt
  Episodes: 10
```

### In Search Results

Search results will reference files using sanitized file IDs in metadata.

## Why This Format?

This format ensures:
1. ✅ **Graphiti Compatibility**: Meets validation rules
2. ✅ **Uniqueness**: Each file has a unique identifier
3. ✅ **Readability**: Still human-readable with dashes and underscores
4. ✅ **Version Support**: Can include version identifiers with `-v-` separator

## Implementation Details

File IDs are sanitized in `episode_manager.py`:
- `sanitize_group_id()` method (line 55): Core sanitization logic
- `create_file_id()` method (line 83): Creates and sanitizes file IDs
- `upload_file()` method (line 191-195): Re-sanitizes after version appending
