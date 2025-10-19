# Vector Search vs Knowledge Graph: Query Comparison

**Dataset**: Medici Founder Agreements (3 founders: Shariq Ali, Aamina Bawany, Eliot Puplett)

## Executive Summary

This document demonstrates when to use **Vector/Semantic Search** vs **Knowledge Graph** queries using real Medici founder agreement data. Both approaches are complementary:

- **Vector Search**: Best for semantic similarity, conceptual understanding, and natural language queries
- **Knowledge Graph**: Best for relationships, comparisons, multi-hop reasoning, and structured analysis

**Key Insight**: The most powerful system uses BOTH approaches together (hybrid retrieval).

---

## 🔍 Vector Search Questions (Semantic Similarity Shines)

These questions leverage embeddings to understand **meaning** and **context**, not just exact keyword matches.

### Conceptual & Semantic Queries

1. **"What are the stock vesting terms?"**
   - Why Vector Wins: Understands "vesting terms" semantically, retrieves all related paragraphs about vesting schedules, cliff periods, and acceleration
   - Returns: Relevant sections across all 3 agreements even with different phrasing

2. **"What happens if a founder leaves the company?"**
   - Why Vector Wins: Maps "leaves the company" → "Service Termination" concept
   - Returns: Unvested Share Repurchase Option clauses, termination consequences

3. **"What are the founders' obligations?"**
   - Why Vector Wins: Understands "obligations" maps to "Provided Services", confidentiality, non-compete
   - Returns: Semantically similar sections about duties and restrictions

4. **"Explain the repurchase rights"**
   - Why Vector Wins: Finds all mentions of buyback, repurchase options, company rights regardless of exact wording
   - Returns: Unvested Share Repurchase Option, exercise conditions, payment terms

5. **"What protections does the company have if a founder stops working?"**
   - Why Vector Wins: Natural language understanding of "protections" → legal safeguards
   - Returns: Repurchase options, vesting acceleration rules, escrow provisions

### Paraphrasing & Intent Recognition

6. **"How long until founders fully own their shares?"**
   - Why Vector Wins: Maps "fully own" → "fully vested" concept
   - Returns: 4-year vesting schedule explanation

7. **"What's the cliff period?"**
   - Why Vector Wins: Understands "cliff" in vesting context
   - Returns: 1-year cliff details (25% vesting)

8. **"Can the company buy back unvested stock?"**
   - Why Vector Wins: Semantic match to repurchase option clauses
   - Returns: Unvested Share Repurchase Option terms

9. **"What are the price per share details?"**
   - Why Vector Wins: Finds all mentions of pricing, valuation, fair market value
   - Returns: $0.00001 per share sections

10. **"What legal jurisdiction governs these agreements?"**
    - Why Vector Wins: Understands legal terminology, finds governing law clauses
    - Returns: Delaware corporation references, choice of law sections

### Finding Similar Concepts Across Documents

11. **"Show me all clauses related to confidentiality"**
    - Why Vector Wins: Finds semantically similar text about proprietary info, NDAs, confidential information
    - Returns: All related sections even if worded differently in each agreement

12. **"What are the tax implications mentioned?"**
    - Why Vector Wins: Semantic understanding of tax-related concepts
    - Returns: 83(b) election references, tax treatment sections

13. **"Are there any anti-dilution provisions?"**
    - Why Vector Wins: Understands financial/legal concept, finds related protective clauses
    - Returns: Adjustment provisions, stock split references

14. **"What are the acceleration triggers for vesting?"**
    - Why Vector Wins: Semantic match to accelerated vesting conditions
    - Returns: Change of control, termination without cause provisions

15. **"Summarize the key terms of these founder agreements"**
    - Why Vector Wins: Retrieves most semantically important passages
    - Returns: Top-ranked sections covering main agreement points

---

## 🕸️ Knowledge Graph Questions (Relationships & Structure Shine)

These questions require understanding **entities**, **relationships**, and **multi-hop reasoning**.

### Entity Relationship Queries

1. **"Who are all the founders of Medici & Company?"**
   - Why Graph Wins: Direct relationship traversal: Company → FOUNDED_BY → [Persons]
   - Returns: Shariq Ali, Aamina Bawany, Eliot Puplett
   - Vector Search Problem: Would return text mentions, not structured list

2. **"Which founder has the most shares?"**
   - Why Graph Wins: Aggregate query across entities with OWNS relationship
   - Returns: Eliot Puplett (2,890,000 shares)
   - Vector Search Problem: Can't aggregate numerical values across documents

3. **"What roles do the founders hold?"**
   - Why Graph Wins: Entity attributes and HAS_ROLE relationships
   - Returns: All three are "Founder" and "Director"
   - Vector Search Problem: Would return text snippets, not structured roles

4. **"Who signed their agreement on the same date?"**
   - Why Graph Wins: Temporal relationship query (SIGNED_ON relationship with date)
   - Returns: All three (01 October 2025)
   - Vector Search Problem: Date comparison across entities is difficult

### Comparison & Aggregation Queries

5. **"Compare the share allocations across all founders"**
   - Why Graph Wins: Structured comparison with exact numbers
   - Returns:
     - Shariq Ali: 2,805,000 shares
     - Aamina Bawany: 2,805,000 shares
     - Eliot Puplett: 2,890,000 shares
   - Vector Search Problem: Can't perform structured comparisons

6. **"What's the total number of founder shares issued?"**
   - Why Graph Wins: Aggregation query (SUM of OWNS relationships)
   - Returns: 8,500,000 total shares
   - Vector Search Problem: Can't sum values across entities

7. **"Do all founders have the same vesting schedule?"**
   - Why Graph Wins: Attribute comparison across entities
   - Returns: Yes - all have 4-year vest with 1-year cliff
   - Vector Search Problem: Hard to definitively compare structured data

8. **"Which founders paid more than $28 for their shares?"**
   - Why Graph Wins: Numerical filtering on entity attributes
   - Returns: Eliot Puplett ($28.90)
   - Vector Search Problem: Numerical comparisons are unreliable

### Multi-Hop Reasoning

9. **"What agreements are associated with Delaware corporations?"**
   - Why Graph Wins: Multi-hop: Agreement → GOVERNS → Company → INCORPORATED_IN → Delaware
   - Returns: All 3 founder agreements
   - Vector Search Problem: Multi-step reasoning is difficult

10. **"Show all legal terms that apply to Shariq Ali"**
    - Why Graph Wins: Graph traversal: Shariq Ali → BOUND_BY → [LegalTerms]
    - Returns: Unvested Share Repurchase Option, Service Termination, Vesting Schedule, etc.
    - Vector Search Problem: Can't definitively link all legal terms to specific person

11. **"What entities are mentioned in founders-contracts classification?"**
    - Why Graph Wins: Classification → CONTAINS → [Documents] → MENTIONS → [Entities]
    - Returns: Medici & Company, 3 founders, Delaware, Docusign, etc.
    - Vector Search Problem: No structural classification metadata

12. **"Which founders have relationships with both Company and Legal Terms?"**
    - Why Graph Wins: Graph pattern matching (Founder)-[FOUNDED]-(Company), (Founder)-[BOUND_BY]-(LegalTerm)
    - Returns: All three founders
    - Vector Search Problem: Can't perform graph pattern matching

### Structural & Hierarchical Queries

13. **"What's the ownership structure of Medici & Company?"**
    - Why Graph Wins: Visualize OWNS relationships with percentages
    - Returns: Ownership graph showing founder equity distribution
    - Vector Search Problem: Can't construct ownership hierarchies

14. **"Find all documents in the founders-contracts classification"**
    - Why Graph Wins: Classification hierarchy traversal
    - Returns: 3 founder agreement PDFs with metadata
    - Vector Search Problem: No classification structure

15. **"Show the network of relationships around Eliot Puplett"**
    - Why Graph Wins: 1-hop or 2-hop graph exploration from entity
    - Returns: Graph showing connections to Company, Shares, Legal Terms, Documents, etc.
    - Vector Search Problem: Can't show relationship networks

### Temporal & Event Queries

16. **"What events happened on October 1, 2025?"**
    - Why Graph Wins: Temporal index query on Event nodes
    - Returns: 3 founder agreement signings
    - Vector Search Problem: Date-based filtering is less precise

17. **"When will the first vesting cliff occur for each founder?"**
    - Why Graph Wins: Temporal calculation from Event relationships
    - Returns: October 1, 2026 for all three
    - Vector Search Problem: Can't perform date arithmetic

---

## ⚖️ Side-by-Side Comparison

| Query Type | Vector Search | Knowledge Graph | Winner |
|------------|---------------|-----------------|--------|
| "What are vesting terms?" | ✅ Semantic understanding | ❌ Requires exact relationships | **Vector** |
| "Who has the most shares?" | ❌ Can't aggregate | ✅ Direct aggregation | **Graph** |
| "Explain repurchase rights" | ✅ Finds similar concepts | ⚠️ Needs pre-defined relationships | **Vector** |
| "Compare all founders' equity" | ❌ No structured comparison | ✅ Structured comparison | **Graph** |
| "What happens if founder leaves?" | ✅ Semantic intent match | ⚠️ Needs TERMINATION relationship | **Vector** |
| "Total shares issued?" | ❌ Can't sum | ✅ Aggregation query | **Graph** |
| "Find confidentiality clauses" | ✅ Semantic similarity | ❌ Needs extracted entities | **Vector** |
| "Founders in Delaware corps?" | ⚠️ Keyword match only | ✅ Multi-hop traversal | **Graph** |
| "Tax implications?" | ✅ Concept understanding | ❌ No structured tax entities | **Vector** |
| "Ownership structure?" | ❌ Can't build hierarchy | ✅ Graph visualization | **Graph** |

---

## 🔄 Hybrid Queries (Best of Both Worlds)

These questions benefit from **combining** vector search and knowledge graph:

1. **"Which founder has the most shares, and what are their vesting terms?"**
   - Graph: Find founder with most shares (Eliot Puplett)
   - Vector: Retrieve vesting terms from Eliot's agreement
   - Result: Structured answer with contextual details

2. **"Compare the repurchase rights across all founders"**
   - Graph: Identify all founders and their agreements
   - Vector: Retrieve semantically similar repurchase clauses
   - Result: Comparative analysis with exact text

3. **"Show me founders who joined after 2024 and their responsibilities"**
   - Graph: Filter by date (October 2025) and get founder list
   - Vector: Semantic search for "responsibilities" → "Provided Services"
   - Result: Filtered list with relevant context

4. **"What legal terms affect all three founders?"**
   - Graph: Find legal terms connected to all 3 entities
   - Vector: Retrieve full clause text for those terms
   - Result: Shared legal obligations with details

5. **"Summarize differences in founder agreements"**
   - Graph: Structural comparison (shares, dates, amounts)
   - Vector: Semantic comparison (clause similarities/differences)
   - Result: Complete comparison report

---

## 📊 When to Use Which Approach

### Use Vector Search When:
- ✅ Questions are in natural language
- ✅ You need semantic understanding (not just keywords)
- ✅ Looking for similar concepts across documents
- ✅ User doesn't know exact terminology
- ✅ Exploratory research ("tell me about...")
- ✅ Summarization tasks

### Use Knowledge Graph When:
- ✅ You need exact counts, sums, or aggregations
- ✅ Comparing entities or attributes
- ✅ Multi-hop reasoning (A → B → C)
- ✅ Relationship-based queries ("who works at...")
- ✅ Structural or hierarchical questions
- ✅ Time-based filtering or calculations
- ✅ Building visualizations or networks

### Use Hybrid (Both) When:
- ✅ Complex analytical questions
- ✅ Need both structure AND context
- ✅ Comparative analysis with details
- ✅ Aggregations with explanations
- ✅ Production RAG systems (always!)

---

## 🎯 Conclusion

**Vector Search** and **Knowledge Graphs** are complementary technologies:

- **Vector Search** = Understanding **meaning** and **context**
- **Knowledge Graph** = Understanding **relationships** and **structure**

**Best Practice**: Use both in a hybrid architecture:
1. Knowledge Graph for entity extraction, relationship mapping, and structured queries
2. Vector Search for semantic retrieval and contextual understanding
3. Combine results for comprehensive question answering

The Medici founder agreements demonstrate this perfectly - questions about concepts and clauses benefit from vector search, while questions about comparisons and relationships benefit from the knowledge graph.
