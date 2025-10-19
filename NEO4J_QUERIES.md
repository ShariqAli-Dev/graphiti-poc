# Neo4j Cypher Queries for Graphiti

## Understanding Graphiti's Schema

Graphiti uses these node types:
- **Entity**: Extracted entities (people, projects, concepts)
- **Episodic**: Episodes you uploaded (files/sections)
- **Community**: Optional groupings of related entities

Relationships:
- **MENTIONS**: Episodic nodes → Entity nodes
- **HAS_EDGE**: Relationships between entities (the facts)
- **MEMBER_OF**: Entity → Community (if communities are built)

---

## Basic Queries to Explore Your Graph

### 1. Count All Nodes by Type

```cypher
MATCH (n)
RETURN labels(n) AS NodeType, count(n) AS Count
ORDER BY Count DESC
```

**What it shows**: How many entities, episodes, etc. you have

---

### 2. View All Entities with Names

```cypher
MATCH (e:Entity)
RETURN e.name AS EntityName,
       e.summary AS Summary,
       labels(e) AS Labels
LIMIT 50
```

**What it shows**: All extracted entities with their names and summaries

**Why names might be missing**: If `e.name` is null, the entity might not have been fully processed

---

### 3. View All Relationships (Edges) Between Entities

```cypher
MATCH (source:Entity)-[r]->(target:Entity)
WHERE type(r) <> 'MEMBER_OF'
RETURN source.name AS From,
       type(r) AS RelationType,
       target.name AS To,
       r.fact AS Fact,
       r.valid_at AS ValidFrom,
       r.invalid_at AS ValidUntil
LIMIT 50
```

**What it shows**: Entity-to-entity relationships with the facts

**This is what you're looking for** - it shows names and relationships!

---

### 4. View Full Graph (Entities + Relationships)

```cypher
MATCH path = (source:Entity)-[r]->(target:Entity)
WHERE type(r) <> 'MEMBER_OF'
RETURN path
LIMIT 100
```

**What it shows**: Visual graph in Neo4j Browser

**Best for**: Seeing the network of entities and how they connect

---

### 5. Find Specific Entity by Name

```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS 'Sarah Chen'
RETURN e.name, e.summary, e.uuid
```

**What it shows**: Find entities matching a name

**Useful for**: Finding specific people or projects

---

### 6. Show All Facts About a Specific Entity

```cypher
MATCH (e:Entity {name: 'Sarah Chen'})-[r]-(other:Entity)
RETURN e.name AS Entity,
       type(r) AS RelationType,
       other.name AS RelatedTo,
       r.fact AS Fact,
       r.valid_at AS ValidFrom,
       r.invalid_at AS ValidUntil
```

**What it shows**: All relationships for Sarah Chen

**Replace 'Sarah Chen'** with any entity name

---

### 7. View All Episodes (Your Uploaded Files)

```cypher
MATCH (ep:Episodic)
RETURN ep.name AS EpisodeName,
       ep.group_id AS FileID,
       ep.source_description AS Metadata,
       ep.created_at AS CreatedAt
ORDER BY ep.created_at DESC
LIMIT 50
```

**What it shows**: All your uploaded file episodes

---

### 8. Show Which Entities Were Mentioned in Which Episodes

```cypher
MATCH (ep:Episodic)-[:MENTIONS]->(e:Entity)
RETURN ep.name AS Episode,
       ep.group_id AS FileID,
       collect(e.name) AS MentionedEntities
LIMIT 20
```

**What it shows**: What entities were extracted from each file

---

### 9. Find Temporal Changes (Facts with Valid/Invalid Dates)

```cypher
MATCH (source:Entity)-[r]->(target:Entity)
WHERE r.valid_at IS NOT NULL OR r.invalid_at IS NOT NULL
RETURN source.name AS From,
       target.name AS To,
       r.fact AS Fact,
       r.valid_at AS ValidFrom,
       r.invalid_at AS ValidUntil
ORDER BY r.valid_at DESC
LIMIT 50
```

**What it shows**: Facts that changed over time (this is Graphiti's temporal feature!)

---

### 10. Full Network Visualization (All Entities)

```cypher
MATCH (e:Entity)
OPTIONAL MATCH (e)-[r]->(other:Entity)
RETURN e, r, other
LIMIT 200
```

**What it shows**: Network graph visualization in Neo4j Browser

**Use this** to see the full knowledge graph visually

---

## Fixing Missing Names/Labels

### If Nodes Have No Names:

```cypher
// Check if names are stored in a different property
MATCH (e:Entity)
RETURN keys(e) AS Properties
LIMIT 1
```

This shows what properties entities have. Names might be in a different field.

### If You Want to See Raw Properties:

```cypher
MATCH (e:Entity)
RETURN e
LIMIT 10
```

This shows the full node with all properties.

---

## Advanced: Finding Specific Patterns

### Find All People Who Changed Roles

```cypher
MATCH (person:Entity)-[r1]->(role1:Entity),
      (person)-[r2]->(role2:Entity)
WHERE r1.fact CONTAINS 'VP'
  AND r2.fact CONTAINS 'CTO'
  AND r1.uuid <> r2.uuid
RETURN person.name AS Person,
       r1.fact AS OldRole,
       r1.valid_at AS OldRoleStart,
       r2.fact AS NewRole,
       r2.valid_at AS NewRoleStart
```

### Find All Projects and Their Status

```cypher
MATCH (project:Entity)
WHERE project.name CONTAINS 'Project'
OPTIONAL MATCH (project)-[r]-(other:Entity)
RETURN project.name AS Project,
       collect(DISTINCT r.fact) AS AllFacts
```

### Find Who Reports to Whom

```cypher
MATCH (person:Entity)-[r]->(manager:Entity)
WHERE r.fact CONTAINS 'reports to'
RETURN person.name AS Employee,
       manager.name AS Manager,
       r.valid_at AS Since
```

---

## Troubleshooting

### If you see nodes with no names in Neo4j Browser:

The visual representation in Neo4j Browser shows the first property it finds. To customize:
1. Click the node type (e.g., "Entity") in the left sidebar
2. Scroll down to "Caption"
3. Select "name" as the caption property

### If relationships have no labels:

Hover over the relationship in Neo4j Browser to see its properties, including `fact`.

### If nothing appears:

Run this to check if data exists:
```cypher
MATCH (n)
RETURN count(n) AS TotalNodes
```

If this returns 0, your upload might have failed or data isn't persisted.

---

## Useful Neo4j Browser Tips

1. **Switch to Graph view**: Click the graph icon (looks like connected dots)
2. **Expand relationships**: Double-click a node to see its connections
3. **See raw data**: Click the table icon to see results as a table
4. **Pin important queries**: Star queries you use often

---

## Example: Full Investigation of Sarah Chen

```cypher
// 1. Find Sarah Chen
MATCH (sarah:Entity {name: 'Sarah Chen'})
RETURN sarah

// 2. Find all her relationships
MATCH (sarah:Entity {name: 'Sarah Chen'})-[r]-(other:Entity)
RETURN sarah, r, other

// 3. Find her career timeline
MATCH (sarah:Entity {name: 'Sarah Chen'})-[r]->(role:Entity)
WHERE r.fact CONTAINS 'position' OR r.fact CONTAINS 'role'
RETURN r.fact AS Fact,
       r.valid_at AS ValidFrom,
       r.invalid_at AS ValidUntil
ORDER BY r.valid_at

// 4. Find which episodes mention her
MATCH (ep:Episodic)-[:MENTIONS]->(sarah:Entity {name: 'Sarah Chen'})
RETURN ep.name, ep.group_id, ep.created_at
ORDER BY ep.created_at
```

---

Run these queries in **Neo4j Browser** (http://localhost:7474) to explore your Graphiti knowledge graph!
