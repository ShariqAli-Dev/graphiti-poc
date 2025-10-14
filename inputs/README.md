# Test Documents for Graphiti CLI

This folder contains sample documents designed to demonstrate Graphiti's **temporal knowledge graph** capabilities.

## Files Overview

Three quarterly reports showing evolving relationships over time:

- **Q1_2024_Report.txt** - Initial state (January 2024)
- **Q2_2024_Report.txt** - First changes (April 2024)
- **Q3_2024_Report.txt** - Major transitions (July 2024)

## What Changes Over Time

These documents track several evolving stories:

### Sarah Chen's Journey

- **Q1**: VP of Engineering
- **Q2**: Promoted to CTO (March 15, 2024)
- **Q3**: Departed for CEO role at startup (July 1, 2024)

### Marcus Rodriguez's Rise

- **Q1**: Senior Engineering Manager (Infrastructure)
- **Q2**: Promoted to VP of Engineering (March 20, 2024)
- **Q3**: Continues as VP, now reports to Interim CTO Jessica Wang

### Project Phoenix Lifecycle

- **Q1**: Planning Phase (start date: Jan 8, 2024)
- **Q2**: LAUNCHED (April 10, 2024) - 25% traffic migrated
- **Q3**: COMPLETED (July 15, 2024) - 100% migration, all targets exceeded

### Team Size Evolution

- **Q1**: 15 engineers
- **Q2**: 22 engineers (growth phase)
- **Q3**: 18 engineers (voluntary departures)

### Budget Changes

- **Q1**: $2.0M
- **Q2**: $2.5M (expansion)
- **Q3**: $2.2M (optimization)

## How to Test

### 1. Upload Documents in Order

```bash
python3 cli.py
# Select option 1: Upload File(s)
# Upload inputs/TC103/Q1_2024_Report.txt
# Then Q2_2024_Report.txt
# Then Q3_2024_Report.txt
```

**Important**: Upload them with dates to test temporal queries:

- Q1_2024_Report.txt - Set reference time to January 15, 2024
- Q2_2024_Report.txt - Set reference time to April 20, 2024
- Q3_2024_Report.txt - Set reference time to July 25, 2024

### 2. Example Questions to Ask

After uploading all three documents, try these searches:

#### Basic Hybrid Search (Option 6, Method 1)

**Testing Current State:**

1. "Who is the VP of Engineering?"

   - Should find Marcus Rodriguez with temporal context

2. "What is the status of Project Phoenix?"

   - Should show COMPLETED with completion date

3. "What is the current engineering team size?"

   - Should prioritize most recent: 18 engineers

4. "What is the current CTO?"
   - Should show Jessica Wang as Interim CTO

**Testing Historical Changes:** 5. "How has the budget changed over time?"

- Should show progression: $2M → $2.5M → $2.2M

6. "What happened to Sarah Chen?"

   - Should show: VP → CTO → Departed

7. "When did Project Phoenix launch?"

   - Should return April 10, 2024

8. "What are the infrastructure cost savings?"
   - Should mention 43% reduction, $215K monthly savings

#### Center Node Search (Option 6, Method 2)

**Explore Entity Relationships:**

9. Search for "Sarah Chen" then use her as center node

   - Query: "career progression" or "projects"
   - Should show promotion, Project Phoenix sponsorship, departure

10. Search for "Project Phoenix" then use it as center node

    - Query: "timeline" or "people involved"
    - Should show Sarah (architect), Marcus (lead), completion details

11. Search for "Marcus Rodriguez" then use him as center node
    - Query: "responsibilities" or "reporting structure"
    - Should show promotion, reports to Jessica Wang

#### Node Search (Option 6, Method 3)

**Find Entity Nodes:**

12. "All projects"

    - Should return Project Phoenix and Project Atlas as entities

13. "Leadership team members"

    - Should return Sarah Chen, Marcus Rodriguez, Jessica Wang, etc.

14. "Engineering managers"

    - Should list Jennifer Wu, Robert Thompson, Amanda Lee

15. "Project Atlas"
    - Should show status, lead (Amanda Lee), Q4 2024 launch

#### Advanced Temporal Questions

16. "Who was VP of Engineering in Q1 2024?"

    - Should return Sarah Chen (with temporal validity)

17. "When did Marcus Rodriguez become VP of Engineering?"

    - Should return March 20, 2024

18. "Why did the team size decrease in Q3?"

    - Should mention voluntary departures, retirements

19. "What was Sarah Chen's role before becoming CTO?"

    - Should return VP of Engineering

20. "Who replaced David Martinez as CTO?"
    - Should show Sarah Chen (March 15, 2024), then Jessica Wang (July 5, 2024)

## What Makes This a Good Test

Graphiti will:

- Track **valid_at** and **invalid_at** timestamps for each fact
- Show that "Sarah Chen is VP of Engineering" is only valid until March 15, 2024
- Maintain relationship history even after people leave
- Allow temporal queries: "who WAS vs who IS"
- Link related entities across time (Sarah → Marcus → Jessica succession)

## Testing File Management Features

### Test Refresh Feature

1. Create a modified version: `Q3_2024_Report_v2.txt` with corrections
2. Use option 5 (Refresh File) to update the knowledge graph
3. Search again to see updated information

### Test Delete Feature

1. Delete Q1_2024_Report using option 2
2. Search for "Sarah Chen VP of Engineering"
3. Should still work (entities remain) but episode is gone

### Test List Files

Use option 3 to see all files grouped by classification (TC103)

## Tips for Your Actual Documents

When uploading your real documents:

1. Organize by TC### classification in folder structure
2. Use version suffixes for updates (filename@Q3_2024)
3. Upload chronologically for best temporal tracking
4. Include dates in document content for temporal extraction
5. Use consistent entity names across documents

Enjoy exploring Graphiti's temporal knowledge graph!
