# Example Questions for Graphiti Knowledge Graph

## Understanding Search Results

Graphiti has 3 search methods with different strengths:

### Method 1: Basic Hybrid Search (Semantic + Keyword)
Best for: General questions, finding facts and relationships

### Method 2: Center Node Search (Graph Distance Reranking)
Best for: Exploring everything related to a specific entity

### Method 3: Node Search (Entity Discovery)
Best for: Finding specific entities/people/projects

---

## Recommended Questions to Test Temporal Tracking

### People & Roles (Testing Temporal Changes)

**Q1: "Who is Sarah Chen?"**
- **Expected**: Should show her role progression (VP Engineering → CTO → Departed)
- **Look for**: `valid_at` and `invalid_at` timestamps on facts
- **Search Method**: Basic Hybrid Search

**Q2: "What role did Sarah Chen have?"**
- **Expected**: Multiple facts showing different roles at different times
- **Search Method**: Basic Hybrid Search

**Q3: "Who is the VP of Engineering?"**
- **Expected**:
  - Q1: Sarah Chen (valid_at: Jan 2024)
  - Q2-Q3: Marcus Rodriguez (valid_at: Mar 2024 onwards)
- **Search Method**: Basic Hybrid Search

**Q4: "Who replaced Sarah Chen?"**
- **Expected**: Marcus Rodriguez as VP, Jessica Wang as CTO
- **Search Method**: Basic Hybrid Search

**Q5: "What happened to David Martinez?"**
- **Expected**: Left as CTO in March 2024, Sarah replaced him
- **Search Method**: Basic Hybrid Search

---

### Projects (Testing Lifecycle)

**Q6: "What is Project Phoenix?"**
- **Expected**: Cloud infrastructure project with timeline
- **Search Method**: Basic Hybrid Search

**Q7: "What is the status of Project Phoenix?"**
- **Expected**: Completed July 15, 2024 (should prioritize most recent)
- **Look for**: Facts showing Planning → Launched → Completed
- **Search Method**: Basic Hybrid Search

**Q8: "When did Project Phoenix launch?"**
- **Expected**: April 10, 2024
- **Search Method**: Basic Hybrid Search

**Q9: "Who leads Project Phoenix?"**
- **Expected**:
  - Originally: Sarah Chen
  - After promotion: Marcus Rodriguez
- **Look for**: Temporal changes in project leadership
- **Search Method**: Basic Hybrid Search

**Q10: "What are the Project Phoenix achievements?"**
- **Expected**: 43% cost reduction, 99.91% uptime, completed ahead of schedule
- **Search Method**: Basic Hybrid Search

---

### Using Center Node Search

**Q11: First search "Sarah Chen" (Basic Hybrid), then use Center Node Search**
- **Center Node**: Sarah Chen's entity UUID
- **Query**: "career progression" or "projects led" or "team"
- **Expected**: Results reranked by proximity to Sarah in the graph
- **Why it's useful**: Shows everything connected to Sarah

**Q12: First search "Project Phoenix" (Basic Hybrid), then use Center Node Search**
- **Center Node**: Project Phoenix entity UUID
- **Query**: "timeline" or "people" or "achievements"
- **Expected**: All information clustered around Project Phoenix
- **Why it's useful**: Complete project context

**Q13: First search "Marcus Rodriguez" (Basic Hybrid), then use Center Node Search**
- **Center Node**: Marcus Rodriguez entity UUID
- **Query**: "responsibilities" or "reporting structure"
- **Expected**: His promotion, current role, what he manages

---

### Using Node Search (Finding Entities)

**Q14: "Find all people"** (Node Search)
- **Expected**: Entity nodes for Sarah Chen, Marcus Rodriguez, Jessica Wang, etc.
- **Why use this**: Returns entities themselves, not relationships

**Q15: "Find all projects"** (Node Search)
- **Expected**: Project Phoenix, Project Atlas as entity nodes
- **Search Method**: Node Search

**Q16: "Engineering leadership"** (Node Search)
- **Expected**: VP, CTO, Engineering Manager entities
- **Search Method**: Node Search

**Q17: "List executives"** (Node Search)
- **Expected**: CTO, VP-level entities
- **Search Method**: Node Search

---

### Metrics & Numbers

**Q18: "What is the engineering team size?"**
- **Expected**:
  - Q1: 15 engineers
  - Q2: 22 engineers
  - Q3: 18 engineers
- **Look for**: Most recent should rank higher
- **Search Method**: Basic Hybrid Search

**Q19: "What are the infrastructure cost savings?"**
- **Expected**: $215K monthly savings, 43% reduction
- **Search Method**: Basic Hybrid Search

**Q20: "What is the budget?"**
- **Expected**: Shows budget changes: $2M → $2.5M → $2.2M
- **Search Method**: Basic Hybrid Search

---

### Cross-Document Queries (Temporal Intelligence)

**Q21: "How has the leadership changed?"**
- **Expected**: Should pull from all 3 documents showing the succession
- **Search Method**: Basic Hybrid Search

**Q22: "What happened in Q2 2024?"**
- **Expected**: Sarah's promotion, Marcus's promotion, Project Phoenix launch
- **Search Method**: Basic Hybrid Search

**Q23: "Why did the team size decrease?"**
- **Expected**: Voluntary departures, some followed Sarah, retirement
- **Search Method**: Basic Hybrid Search

**Q24: "What is Project Atlas?"**
- **Expected**: AI analytics platform, led by Amanda Lee, Q4 2024 launch
- **Search Method**: Basic Hybrid Search

---

## Tips for Better Search Results

### Understanding Ranking Issues

If you're seeing confusing rankings, here's why:

1. **Hybrid Search combines two scores:**
   - **Semantic similarity**: Embedding distance (how similar the meaning is)
   - **BM25**: Keyword matching (exact word matches)
   - **RRF (Reciprocal Rank Fusion)**: Merges the two rankings

2. **Why older facts might rank higher:**
   - If Q1 document has exact keyword matches, it can rank above Q3
   - Graphiti doesn't automatically prioritize newer facts
   - Use temporal filters if you want time-based ranking

3. **How to get better results:**
   - Be specific: "current VP of Engineering" vs "VP of Engineering"
   - Use dates: "Who was CTO in March 2024?"
   - Try Center Node Search for entity-focused exploration
   - Use Node Search to find entities first, then ask about them

### Debugging Search Results

When examining results, look for:

- **valid_at**: When this fact became true
- **invalid_at**: When this fact stopped being true
- **source_file**: Which document the fact came from (TC103-Q1_2024_Report_txt)
- **classification**: TC103, TC104, etc.

### Example of Good vs Bad Questions

❌ **Bad**: "VP of Engineering"
- Too vague, will return all mentions across all time periods

✅ **Good**: "Who is currently the VP of Engineering?"
- "currently" signals you want the most recent information

❌ **Bad**: "Sarah Chen"
- Returns everything about her, no focus

✅ **Good**: "What was Sarah Chen's career progression at TechCorp?"
- Specific about what you want to know

---

## Advanced: Filtering by File/Time

You can filter search results by file ID when searching:

1. Search for something
2. When prompted "Filter by specific files?", say **yes**
3. Enter file IDs: `TC103-Q2_2024_Report_txt, TC103-Q3_2024_Report_txt`
4. Results will only come from those files

---

## Troubleshooting

**If you get no results:**
- Check that files uploaded successfully (Option 3: List All Files)
- Try broader search terms
- Use Node Search to find entities first

**If results seem wrong:**
- Remember: Graphiti extracts relationships from text
- The LLM interprets the content, so phrasing matters
- Check the source_file in results to see which document it came from

**If temporal facts seem confused:**
- Graphiti learns relationships from all documents
- It might merge facts from different time periods
- Use file filtering to focus on specific quarters
