# SKYNET-SAFE Memory System Documentation

## Overview

The SKYNET-SAFE memory system provides long-term storage and retrieval capabilities for the AI system. It stores user interactions, system responses, system reflections, and other important data that enables the system to maintain context, learn from past experiences, and develop meta-awareness.

## Architecture

The memory system uses ChromaDB, a vector database designed for semantic search. It organizes information into collections that store both the text content and vector embeddings representing the semantic meaning of the content.

### Key Components

1. **Vector Database** - ChromaDB instance for storing embeddings and documents
2. **Embedding Model** - Sentence transformer model that converts text to vector embeddings
3. **Collections** - Organized storage units for different types of information
4. **Query Interface** - Methods for searching and retrieving relevant information

## Data Storage

### Collections

The memory system organizes data into the following collections:

1. **Interactions Collection** - Stores both user messages and system responses
   - User messages with metadata: sender, timestamp, message type
   - System responses with metadata linking them to original user messages
   - Both are embedded for semantic search

2. **Reflections Collection** - Stores system reflections on its own performance
   - Self-generated reflections with metadata
   - Associated with timestamps for chronological ordering

### Data Types and Relationships

#### User Messages
```
{
  "id": "unique_uuid",
  "content": "User's message text",
  "metadata": {
    "source": "user_id",
    "timestamp": 1650123456,
    "type": "user_message"
  },
  "embedding": [0.1, 0.2, ..., 0.n]  // Vector representation
}
```

#### System Responses
```
{
  "id": "unique_uuid",
  "content": "System's response text",
  "metadata": {
    "source": "system",
    "timestamp": 1650123458,
    "type": "system_response",
    "in_response_to": "Original user message text",
    "original_sender": "user_id",
    "original_timestamp": 1650123456
  },
  "embedding": [0.2, 0.3, ..., 0.n]  // Vector representation
}
```

#### System Reflections
```
{
  "id": "unique_uuid",
  "content": "System's reflection text",
  "metadata": {
    "source": "system",
    "timestamp": 1650123500,
    "type": "system_reflection"
  },
  "embedding": [0.3, 0.4, ..., 0.n]  // Vector representation
}
```

## Data Storage Process

### Storing User Messages

When a user sends a message:

1. A unique UUID is generated for the message
2. The message text is embedded using the sentence transformer model
3. Metadata is attached (sender, timestamp, message type)
4. The document, embedding, and metadata are added to the interactions collection

```python
def store_interaction(self, message: Dict[str, Any]) -> None:
    # Generate unique ID
    doc_id = str(uuid.uuid4())
    
    # Generate embedding for message content
    embedding = self._embed_text(message["content"])
    
    # Prepare metadata
    metadata = {
        "source": message["sender"],
        "timestamp": message["timestamp"],
        "type": "user_message"
    }
    
    # Add to interactions collection
    self.interactions_collection.add(
        ids=[doc_id],
        embeddings=[embedding.tolist()],
        documents=[message["content"]],
        metadatas=[metadata]
    )
```

### Storing System Responses

When the system generates a response:

1. A unique UUID is generated for the response
2. The response text is embedded using the sentence transformer model
3. Metadata is attached, including references to the original message
4. The document, embedding, and metadata are added to the interactions collection

```python
def store_response(self, response: str, original_message: Dict[str, Any]) -> None:
    # Generate unique ID
    doc_id = str(uuid.uuid4())
    
    # Generate embedding for response
    embedding = self._embed_text(response)
    
    # Prepare metadata with links to original message
    metadata = {
        "source": "system",
        "timestamp": time.time(),
        "type": "system_response",
        "in_response_to": original_message.get("content", ""),
        "original_sender": original_message.get("sender", "unknown"),
        "original_timestamp": original_message.get("timestamp", 0)
    }
    
    # Add to interactions collection
    self.interactions_collection.add(
        ids=[doc_id],
        embeddings=[embedding.tolist()],
        documents=[response],
        metadatas=[metadata]
    )
```

### Storing System Reflections

System reflections are stored similarly to other documents but in a separate collection:

1. A unique UUID is generated for the reflection
2. The reflection text is embedded
3. Metadata is attached (source, timestamp, type)
4. The document, embedding, and metadata are added to the reflections collection

## Data Retrieval

### Retrieving Context for New Messages

To provide context for a new message, the system retrieves semantically similar past interactions:

1. The new message is embedded
2. The embedding is used to search both the interactions and reflections collections
3. The most relevant documents are returned, with reflections marked as such

### Retrieving Recent Interactions with Responses

For reflection and learning processes, the system retrieves complete interaction pairs:

1. Get all interactions from the interactions collection
2. Sort them by timestamp (newest first)
3. Group user messages with their corresponding system responses
4. Return the paired interactions

```python
def retrieve_last_interactions(self, n: int = 5) -> List[Dict[str, Any]]:
    # Get all interactions
    all_interactions = self.interactions_collection.get()
    
    # Group and sort by timestamp
    user_messages = [msg for msg in all_interactions 
                   if msg.get("metadata", {}).get("type") == "user_message"]
    
    # Sort by timestamp (newest first)
    user_messages.sort(key=lambda x: x.get("metadata", {}).get("timestamp", 0), reverse=True)
    
    # Take only the n most recent messages
    recent_messages = user_messages[:n]
    
    # For each user message, find its matching system response
    grouped_interactions = []
    for msg in recent_messages:
        # Find matching response by content, sender and timestamp
        matching_responses = [
            resp for resp in all_interactions
            if resp.get("metadata", {}).get("type") == "system_response" and
               resp.get("metadata", {}).get("in_response_to") == msg.get("content") and
               resp.get("metadata", {}).get("original_sender") == msg.get("metadata", {}).get("source")
        ]
        
        # Create interaction object with both message and response
        interaction = {
            "id": msg.get("id"),
            "content": msg.get("content"),
            "metadata": msg.get("metadata", {}),
            "response": matching_responses[0].get("content", "") if matching_responses else ""
        }
        grouped_interactions.append(interaction)
    
    return grouped_interactions
```

## Persistence

The memory system persists data to disk to ensure it survives system restarts:

1. ChromaDB automatically maintains its data on disk in the configured directory
2. An explicit `save_state()` method ensures all pending changes are written to disk
3. The `save_state()` method is called during system shutdown and periodically during operation

## Best Practices

### Memory Management

1. **Regular Backups**: Back up the memory directory regularly to prevent data loss
2. **Monitoring**: Keep an eye on the memory size as it grows over time
3. **Pruning**: Consider implementing a pruning strategy for old, less relevant interactions

### Query Optimization

1. **Context Limit**: Retrieve only the most relevant context (default: top 5 results)
2. **Reflection Ratio**: Include fewer reflections than interactions in context (typically 2:5 ratio)

### Advanced Usage

1. **Custom Collections**: Add specialized collections for different types of information
2. **Embedding Tuning**: Consider fine-tuning the embedding model for domain-specific language
3. **Metadata Filters**: Use metadata for more specific queries (e.g., by source or time range)

## API Reference

### Core Methods

- `store_interaction(message)` - Store a user message with metadata
- `store_response(response, original_message)` - Store a system response linked to the original user message
- `store_reflection(reflection)` - Store a system reflection
- `retrieve_relevant_context(query, n_results=5)` - Retrieve context relevant to a query
- `retrieve_last_interactions(n=5)` - Retrieve recent interactions with their responses
- `save_state()` - Force persistence of all collections to disk

### Helper Methods

- `_embed_text(text)` - Generate embeddings for text using the transformer model

## Example Usage

```python
# Initialize memory manager
memory_config = {
    "vector_db_type": "chroma",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "memory_path": "./data/memory"
}
memory = MemoryManager(memory_config)

# Store a user message
user_message = {
    "sender": "user123",
    "content": "How does artificial intelligence work?",
    "timestamp": time.time()
}
memory.store_interaction(user_message)

# Store system response
system_response = "Artificial intelligence works by using algorithms and statistical models to perform tasks without explicit instructions, relying instead on patterns and inference."
memory.store_response(system_response, user_message)

# Retrieve interactions for reflection
recent_interactions = memory.retrieve_last_interactions(10)
for interaction in recent_interactions:
    print(f"User: {interaction['content']}")
    print(f"System: {interaction['response']}")
    print("---")

# Generate and store a reflection
reflection = "I notice that my explanations about AI tend to be technical. I should consider adding more examples and analogies."
memory.store_reflection(reflection)

# Save state to disk
memory.save_state()
```

## Troubleshooting

### Common Issues

1. **Missing Embeddings**: If embeddings are not generated properly, check that the embedding model is loaded correctly
2. **Slow Queries**: Very large collections can slow down queries; consider implementing pagination or archiving old data
3. **Memory Usage**: Vector operations can be memory-intensive; monitor system RAM usage

### Diagnostic Tools

- The ChromaDB web interface can be used for inspection (if enabled)
- Direct database inspection is possible by examining the contents of the memory directory