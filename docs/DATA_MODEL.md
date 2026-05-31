# CodeLens Data Model

## Graph Overview

```mermaid
flowchart LR

    File -->|contains| Class
    File -->|contains| Interface
    File -->|contains| Function

    Class -->|contains| Function
    Class -->|contains| Constructor

    Class -->|extends| Unresolved
    Class -->|implements| Unresolved

    Function -->|calls| Function
    Function -->|has_branch| ConditionalBranch
    Function -->|returns| ReturnStatement

    File -->|imports| Unresolved
```

## Node Types

| Node Type | Purpose |
|------------|------------|
| File | Source file |
| Class | Class declaration |
| Interface | Interface declaration |
| Function | Method or standalone function |
| Constructor | Constructor definition |
| ConditionalBranch | if / else / switch branch |
| ReturnStatement | Return statement |
| Unresolved | Placeholder unresolved target |

## Common Node Properties

All graph nodes are represented by the `CodeNode` model.

| Property | Description |
|-----------|-------------|
| uid | Globally unique identifier |
| name | Symbol name |
| qualified_name | Fully-qualified symbol name |
| node_type | Node category |
| filepath | Relative repository path |
| start_line | Start line number |
| end_line | End line number |
| docstring | Documentation text (optional) |
| signature | Function/constructor signature (optional) |
| file_hash | Source file hash used for incremental indexing |

## Relationship Types

| Relationship | Meaning |
|-------------|----------|
| contains | Parent-child ownership |
| calls | Function invocation |
| imports | File dependency |
| implements | Class implements interface |
| extends | Class inheritance |
| has_branch | Function owns a conditional branch |
| returns | Function returns a value |

**Note:** `extends` and `implements` relationships currently resolve to placeholder `Unresolved` nodes until full symbol resolution is implemented.

## Graph Storage Models

### CodeNode

Represents a code entity extracted from the AST.

### CodeEdge

Represents a directed relationship between two nodes.

### ParseResult

Represents the extraction result of a parsed source file.