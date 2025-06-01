"""Long-term memory management module."""

import logging
import os
import json
import uuid
import time
from typing import Dict, List, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger("SKYNET-SAFE.MemoryManager")


class MemoryManager:
    """Class for managing the system's long-term memory."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize long-term memory.
        
        Args:
            config: Memory configuration containing vector database type, embedding model, etc.
        """
        self.config = config
        logger.info(f"Initializing long-term memory...")
        
        # Ensure memory directory exists
        os.makedirs(config["memory_path"], exist_ok=True)
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(config["embedding_model"])
            logger.info(f"Embedding model {config['embedding_model']} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
        
        # Initialize vector database
        try:
            if config["vector_db_type"] == "chroma":
                self.db = chromadb.Client(chromadb.config.Settings(
                    persist_directory=os.path.join(config["memory_path"], "chroma_db")
                ))
                # Create or get collection for interactions
                self.interactions_collection = self.db.get_or_create_collection(
                    name="interactions",
                    embedding_function=None  # We provide our own embeddings
                )
                
                # Create or get collection for reflections
                self.reflections_collection = self.db.get_or_create_collection(
                    name="reflections",
                    embedding_function=None  # We provide our own embeddings
                )
            else:
                raise ValueError(f"Unsupported vector database type: {config['vector_db_type']}")
                
            logger.info(f"Vector database {config['vector_db_type']} initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            raise
    
    def store_interaction(self, message: Dict[str, Any]) -> None:
        """Store an interaction in memory.
        
        Args:
            message: Message containing sender, content, and timestamp
        """
        try:
            # Generate unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # Generate embedding for the message content
            embedding = self._embed_text(message["content"])
            
            # Prepare metadata
            metadata = {
                "source": message["sender"],
                "timestamp": message["timestamp"],
                "type": "user_message"
            }
            
            # Add document to interactions collection
            self.interactions_collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[message["content"]],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored interaction from {message['sender']} in memory")
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            
    def store_response(self, response: str, original_message: Dict[str, Any]) -> None:
        """Store system response in memory.
        
        Args:
            response: System response content
            original_message: Original message that was responded to
        """
        try:
            # Generate unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # Generate embedding for the response
            embedding = self._embed_text(response)
            
            # Prepare metadata
            metadata = {
                "source": "system",
                "timestamp": time.time(),
                "type": "system_response",
                "in_response_to": original_message.get("content", ""),
                "original_sender": original_message.get("sender", "unknown"),
                "original_timestamp": original_message.get("timestamp", 0)
            }
            
            # Add document to interactions collection
            self.interactions_collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[response],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored system response in memory")
            
        except Exception as e:
            logger.error(f"Error storing response: {e}")
    
    def store_reflection(self, reflection: str) -> None:
        """Store reflection in memory.
        
        Args:
            reflection: Reflection to store
        """
        try:
            # Generate unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # Generate embedding for the reflection
            embedding = self._embed_text(reflection)
            
            # Prepare metadata
            metadata = {
                "source": "system",
                "timestamp": time.time(),
                "type": "system_reflection"
            }
            
            # Add document to reflections collection
            self.reflections_collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[reflection],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored system reflection in memory")
            
        except Exception as e:
            logger.error(f"Error storing reflection: {e}")
    
    def retrieve_relevant_context(self, query: str, n_results: int = 5) -> List[str]:
        """Retrieve context from memory based on a query.
        
        Args:
            query: Query for which we're looking for context
            n_results: Number of results to retrieve
            
        Returns:
            List of documents forming the context
        """
        try:
            # Generate embedding for the query
            query_embedding = self._embed_text(query)
            
            # Search for similar documents in the interactions collection
            interactions_results = self.interactions_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            # Search for similar documents in the reflections collection
            reflections_results = self.reflections_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=2  # Fewer reflections than interactions
            )
            
            # Combine results
            context = []
            
            # Add interactions
            if interactions_results["documents"] and len(interactions_results["documents"]) > 0:
                context.extend(interactions_results["documents"][0])
                logger.debug(f"Retrieved {len(interactions_results['documents'][0])} interactions for context")
            else:
                logger.debug("No interactions found in memory for context")
            
            # Add reflections
            if reflections_results["documents"] and len(reflections_results["documents"]) > 0:
                # Prefix reflections with a marker
                for reflection in reflections_results["documents"][0]:
                    context.append("SYSTEM REFLECTION: " + reflection)
                logger.debug(f"Retrieved {len(reflections_results['documents'][0])} reflections for context")
            else:
                logger.debug("No reflections found in memory for context")
            
            logger.debug(f"Total context items retrieved: {len(context)} for query: {query[:50]}...")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def retrieve_last_interactions(self, n: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent interactions.
        
        Args:
            n: Number of recent interactions to retrieve
            
        Returns:
            List of recent interactions, for each user query
            we also include the system response (if it exists)
        """
        try:
            # Retrieve all interactions
            results = self.interactions_collection.get()
            
            # Convert to list of dictionaries
            all_interactions = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    all_interactions.append({
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i] if "metadatas" in results else {}
                    })
            
            # Sort by timestamp (newest first)
            all_interactions.sort(key=lambda x: x.get("metadata", {}).get("timestamp", 0), reverse=True)
            
            # Group queries with their responses
            grouped_interactions = []
            user_messages = [msg for msg in all_interactions if msg.get("metadata", {}).get("type") == "user_message"]
            
            for user_msg in user_messages[:n]:  # Take only n newest user queries
                # Look for system response to this query
                content = user_msg.get("content", "")
                user_id = user_msg.get("metadata", {}).get("source", "")
                user_timestamp = user_msg.get("metadata", {}).get("timestamp", 0)
                
                # Look for matching system response
                matching_responses = [
                    msg for msg in all_interactions 
                    if msg.get("metadata", {}).get("type") == "system_response" and
                       msg.get("metadata", {}).get("in_response_to") == content and
                       msg.get("metadata", {}).get("original_sender") == user_id and
                       msg.get("metadata", {}).get("original_timestamp") == user_timestamp
                ]
                
                # Create interaction with query and response
                interaction = {
                    "id": user_msg.get("id"),
                    "content": content,
                    "metadata": user_msg.get("metadata", {}),
                    "response": matching_responses[0].get("content", "") if matching_responses else ""
                }
                grouped_interactions.append(interaction)
            
            return grouped_interactions
            
        except Exception as e:
            logger.error(f"Error retrieving recent interactions: {e}")
            return []
    
    def retrieve_recent_interactions(self, n: int = 10) -> List[Dict[str, Any]]:
        """Alias for retrieve_last_interactions for naming consistency."""
        return self.retrieve_last_interactions(n)
    
    def get_conversation_context(self, n_pairs: int = 5) -> List[str]:
        """Pobierz ostatnie N wypowiedzi Juno jako kontekst konwersacyjny.
        
        Args:
            n_pairs: Liczba ostatnich wypowiedzi Juno do pobrania
            
        Returns:
            Lista stringów z wypowiedziami Juno (od najstarszej do najnowszej)
        """
        try:
            recent_interactions = self.retrieve_last_interactions(n=n_pairs)
            context = []
            
            if recent_interactions:
                logger.debug(f"Building conversation context from {len(recent_interactions)} interactions")
                
                # Zbierz tylko odpowiedzi Juno, odwróć kolejność (najstarsza -> najnowsza)
                juno_responses = []
                for interaction in reversed(recent_interactions):  # Odwróć żeby mieć od najstarszej
                    system_response = interaction.get('response', '')
                    if system_response:
                        juno_responses.append(system_response)
                
                context = juno_responses
                logger.debug(f"Generated {len(context)} Juno response context items")
            else:
                logger.debug("No recent interactions found for conversation context")
            
            return context
            
        except Exception as e:
            logger.error(f"Error building conversation context: {e}")
            return []
    
    def get_hybrid_context(self, query: str, config: Dict[str, Any]) -> List[str]:
        """Pobierz hybrydowy kontekst łączący semantic search i conversation history.
        
        Args:
            query: Zapytanie użytkownika
            config: Konfiguracja pamięci z MEMORY sekcji
            
        Returns:
            Lista kontekstu łącząca semantic i conversation context
        """
        try:
            context = []
            
            # Sprawdź strategię kontekstu
            strategy = config.get("context_strategy", "hybrid")
            
            if strategy in ["semantic", "hybrid"]:
                # Pobierz kontekst semantyczny
                max_semantic = config.get("max_semantic_results", 3)
                semantic_context = self.retrieve_relevant_context(query, n_results=max_semantic)
                
                if semantic_context:
                    context.extend(semantic_context)
                    logger.debug(f"Added {len(semantic_context)} semantic context items")
            
            if strategy in ["conversation", "hybrid"]:
                # Sprawdź czy pamięć konwersacyjna jest włączona
                conv_config = config.get("conversation_memory", {})
                if conv_config.get("enabled", True) and conv_config.get("include_in_prompt", True):
                    
                    max_pairs = config.get("max_conversation_pairs", 5)
                    conversation_context = self.get_conversation_context(n_pairs=max_pairs)
                    
                    if conversation_context:
                        # Dodaj naturalny opis kontekstu
                        context.append("Do tej pory wypowiedziałaś następujące kwestie:")
                        context.extend(conversation_context)
                        logger.debug(f"Added {len(conversation_context)} conversation context items")
            
            logger.debug(f"Generated hybrid context with {len(context)} total items")
            return context
            
        except Exception as e:
            logger.error(f"Error building hybrid context: {e}")
            return []
    
    def save_state(self) -> None:
        """Save memory state."""
        try:
            if hasattr(self, 'db'):
                logger.info("Saving memory state...")
                # Use db.persist() instead of collection.persist()
                # as collection may not have persist method in newer ChromaDB versions
                self.db.persist()
                logger.info("Memory state saved successfully")
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
    
    def _embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text.
        
        Args:
            text: Text to convert to embedding
            
        Returns:
            Embedding vector
        """
        return self.embedding_model.encode(text)
