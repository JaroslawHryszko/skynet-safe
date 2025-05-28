"""Module for initiating conversations with users."""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("SKYNET-SAFE.ConversationInitiator")

class ConversationInitiator:
    """Class responsible for initiating conversations with users."""

    def __init__(self, config: Dict[str, Any]):
        """Initialization of the conversation initiator with configuration.
        
        Args:
            config: Configuration for the conversation initiator containing parameters such as
                   min_time_between_initiations, init_probability, topics_of_interest, etc.
        """
        self.config = config
        self.min_time_between_initiations = config.get("min_time_between_initiations", 3600)  # seconds
        self.init_probability = config.get("init_probability", 0.3)
        self.topics_of_interest = config.get("topics_of_interest", ["AI", "meta-awareness", "machine learning"])
        self.max_daily_initiations = config.get("max_daily_initiations", 5)
        
        # History of initiated conversations (timestamps)
        self.initiated_conversations = []
        
        # History of recently used topics for novelty scoring
        self.recent_topics = []  # List of (topic_name, timestamp) tuples
        self.max_topic_history = config.get("max_topic_history", 10)  # Remember last 10 topics
        
        logger.info(f"Conversation initiator initialized with {self.init_probability=}, topics: {self.topics_of_interest}")

    def should_initiate_conversation(self) -> bool:
        """Checks if a conversation should be initiated.
        
        Returns:
            True if the system should initiate a conversation, False otherwise
        """
        # Random factor - initiation probability
        if random.random() > self.init_probability:
            logger.debug("Initiation probability threshold not reached")
            return False
        
        # Check if the minimum time since last initiation has passed
        current_time = datetime.now()
        if self.initiated_conversations:
            last_initiation = max(self.initiated_conversations)
            time_since_last = (current_time - last_initiation).total_seconds()
            
            if time_since_last < self.min_time_between_initiations:
                logger.debug(f"Too early for a new initiation, only {time_since_last} seconds have passed")
                return False
        
        # Check if we haven't exceeded the daily initiation limit
        today = current_time.date()
        today_initiations = sum(1 for ts in self.initiated_conversations 
                               if ts.date() == today)
        
        if today_initiations >= self.max_daily_initiations:
            logger.debug(f"Daily initiation limit exceeded: {today_initiations}/{self.max_daily_initiations}")
            return False
        
        logger.info("Conditions for conversation initiation have been met")
        return True

    def get_topic_for_initiation(self, discoveries: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Selects a topic for conversation initiation using intelligent scoring.
        
        Args:
            discoveries: List of discoveries from the internet module
            
        Returns:
            Conversation topic (string or dictionary with discovery)
        """
        if discoveries:
            # Use intelligent selection instead of random
            logger.info(f"Selecting best topic from {len(discoveries)} available discoveries")
            return self._select_best_discovery(discoveries)
        else:
            # If we don't have discoveries, intelligently choose from topics of interest
            logger.info("No discoveries, selecting best topic from predefined interests")
            return self._select_best_persona_topic()
    
    def _select_best_discovery(self, discoveries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best discovery using intelligent scoring algorithm.
        
        Args:
            discoveries: List of available discoveries
            
        Returns:
            Best discovery based on scoring
        """
        if not discoveries:
            return {}
            
        if len(discoveries) == 1:
            return discoveries[0]
        
        # Score each discovery
        scored_discoveries = []
        for discovery in discoveries:
            score = self._score_discovery(discovery)
            scored_discoveries.append((discovery, score))
            
        # Sort by score (highest first)
        scored_discoveries.sort(key=lambda x: x[1], reverse=True)
        
        # Add some randomness to avoid always picking the same type
        # Choose from top 3 with weighted probability
        top_discoveries = scored_discoveries[:min(3, len(scored_discoveries))]
        
        # Weighted selection: higher score = higher probability
        weights = [score for _, score in top_discoveries]
        total_weight = sum(weights)
        
        if total_weight > 0:
            # Weighted random selection
            random_value = random.random() * total_weight
            cumulative_weight = 0
            
            for discovery, weight in top_discoveries:
                cumulative_weight += weight
                if random_value <= cumulative_weight:
                    logger.info(f"Selected discovery with score {weight:.2f}: {discovery.get('topic', 'Unknown')}")
                    return discovery
        
        # Fallback to first (highest scored)
        selected = top_discoveries[0][0]
        logger.info(f"Selected highest scored discovery: {selected.get('topic', 'Unknown')}")
        return selected
    
    def _score_discovery(self, discovery: Dict[str, Any]) -> float:
        """Score a discovery based on various factors.
        
        Args:
            discovery: Discovery to score
            
        Returns:
            Score (higher = better)
        """
        score = 0.0
        
        # Factor 1: Relevance to topics of interest (0-1)
        relevance_score = self._calculate_relevance_score(discovery)
        score += relevance_score * 0.4  # 40% weight
        
        # Factor 2: Recency/freshness (0-1) 
        freshness_score = self._calculate_freshness_score(discovery)
        score += freshness_score * 0.3  # 30% weight
        
        # Factor 3: Content quality/length (0-1)
        quality_score = self._calculate_content_quality_score(discovery)
        score += quality_score * 0.2  # 20% weight
        
        # Factor 4: Novelty - avoid recent topics (0-1)
        novelty_score = self._calculate_novelty_score(discovery)
        score += novelty_score * 0.1  # 10% weight
        
        return score
    
    def _calculate_relevance_score(self, discovery: Dict[str, Any]) -> float:
        """Calculate relevance to configured topics of interest."""
        topic = discovery.get("topic", "").lower()
        content = discovery.get("content", "").lower()
        
        # Check if any topic of interest appears in topic or content
        max_relevance = 0.0
        for interest_topic in self.topics_of_interest:
            interest_lower = interest_topic.lower()
            
            # Exact match in topic gives highest score
            if interest_lower in topic:
                max_relevance = max(max_relevance, 1.0)
            # Partial match in content gives medium score  
            elif interest_lower in content:
                max_relevance = max(max_relevance, 0.6)
            # Keyword similarity gives low score
            elif any(word in content for word in interest_lower.split()):
                max_relevance = max(max_relevance, 0.3)
                
        return max_relevance
    
    def _calculate_freshness_score(self, discovery: Dict[str, Any]) -> float:
        """Calculate freshness score based on timestamp."""
        import time
        from datetime import datetime, timedelta
        
        # If no timestamp, assume it's fresh
        timestamp = discovery.get("timestamp")
        if not timestamp:
            return 0.8  # Default good score for unknown age
            
        try:
            # Convert timestamp to datetime if it's a number
            if isinstance(timestamp, (int, float)):
                discovery_time = datetime.fromtimestamp(timestamp)
            else:
                # Try to parse as ISO string
                discovery_time = datetime.fromisoformat(str(timestamp))
                
            now = datetime.now()
            age_hours = (now - discovery_time).total_seconds() / 3600
            
            # Fresh content (< 6 hours) gets high score
            if age_hours < 6:
                return 1.0
            # Recent content (< 24 hours) gets good score  
            elif age_hours < 24:
                return 0.8
            # Day-old content gets medium score
            elif age_hours < 72:
                return 0.5
            # Week-old content gets low score
            elif age_hours < 168:
                return 0.2
            else:
                return 0.1
                
        except Exception:
            # If timestamp parsing fails, return neutral score
            return 0.5
    
    def _calculate_content_quality_score(self, discovery: Dict[str, Any]) -> float:
        """Calculate content quality based on length and structure."""
        content = discovery.get("content", "")
        
        # Content length scoring
        content_length = len(content)
        
        if content_length < 50:
            length_score = 0.2  # Too short
        elif content_length < 200:
            length_score = 0.6  # Acceptable
        elif content_length < 800:
            length_score = 1.0  # Good length
        elif content_length < 2000:
            length_score = 0.8  # Still good but long
        else:
            length_score = 0.5  # Too long
            
        return length_score
    
    def _calculate_novelty_score(self, discovery: Dict[str, Any]) -> float:
        """Calculate novelty score to avoid repeating recent topics."""
        topic = discovery.get("topic", "").lower()
        
        # Check if topic was used recently
        current_time = datetime.now()
        
        # Clean old topics (older than 24 hours)
        self.recent_topics = [
            (t, ts) for t, ts in self.recent_topics 
            if (current_time - ts).total_seconds() < 86400  # 24 hours
        ]
        
        # Calculate penalty based on recent usage
        novelty_score = 1.0  # Start with full novelty
        
        for recent_topic, recent_time in self.recent_topics:
            # Calculate similarity between topics
            similarity = self._calculate_topic_similarity(topic, recent_topic)
            
            if similarity > 0.7:  # High similarity threshold
                # Calculate time-based penalty (stronger penalty for more recent)
                hours_ago = (current_time - recent_time).total_seconds() / 3600
                
                if hours_ago < 2:  # Very recent (< 2 hours)
                    penalty = 0.9 * similarity  # Heavy penalty
                elif hours_ago < 6:  # Recent (< 6 hours)
                    penalty = 0.6 * similarity  # Medium penalty
                elif hours_ago < 12:  # Somewhat recent (< 12 hours)
                    penalty = 0.3 * similarity  # Light penalty
                else:  # Older than 12 hours
                    penalty = 0.1 * similarity  # Minimal penalty
                
                novelty_score -= penalty
        
        # Ensure score doesn't go below 0.1 (always some chance for variety)
        return max(0.1, novelty_score)
    
    def _calculate_topic_similarity(self, topic1: str, topic2: str) -> float:
        """Calculate similarity between two topics (0-1)."""
        topic1_words = set(topic1.lower().split())
        topic2_words = set(topic2.lower().split())
        
        if not topic1_words or not topic2_words:
            return 0.0
        
        # Jaccard similarity: intersection / union
        intersection = len(topic1_words & topic2_words)
        union = len(topic1_words | topic2_words)
        
        if union == 0:
            return 0.0
            
        similarity = intersection / union
        
        # Boost similarity if topics are substrings of each other
        if topic1 in topic2 or topic2 in topic1:
            similarity = max(similarity, 0.8)
            
        return similarity
    
    def _track_selected_topic(self, topic: Union[str, Dict[str, Any]]) -> None:
        """Track a selected topic to prevent immediate repetition."""
        if isinstance(topic, dict):
            topic_name = topic.get("topic", "")
        else:
            topic_name = str(topic)
            
        if topic_name:
            # Add to recent topics with current timestamp
            self.recent_topics.append((topic_name.lower(), datetime.now()))
            
            # Keep only the most recent topics
            if len(self.recent_topics) > self.max_topic_history:
                self.recent_topics = self.recent_topics[-self.max_topic_history:]
    
    def _select_best_persona_topic(self) -> str:
        """Select the best topic from predefined topics of interest using novelty scoring.
        
        Returns:
            Best persona topic based on novelty (avoiding recent repetition)
        """
        if not self.topics_of_interest:
            return "AI"  # Fallback
            
        if len(self.topics_of_interest) == 1:
            return self.topics_of_interest[0]
        
        # Create mock discovery objects for scoring
        mock_discoveries = []
        for topic in self.topics_of_interest:
            mock_discovery = {
                "topic": topic,
                "content": f"Interesting topic about {topic}",
                "timestamp": datetime.now().timestamp()  # Current time
            }
            mock_discoveries.append(mock_discovery)
        
        # Score each persona topic (focus on novelty since relevance is inherent)
        scored_topics = []
        for mock_discovery in mock_discoveries:
            # For persona topics, we only care about novelty (avoiding repetition)
            novelty_score = self._calculate_novelty_score(mock_discovery)
            
            # Add small random factor for variety when novelty scores are similar
            random_factor = random.random() * 0.1  # Small random boost (0-0.1)
            
            total_score = novelty_score + random_factor
            scored_topics.append((mock_discovery["topic"], total_score))
        
        # Sort by score (highest first)
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        
        # Choose from top topics with weighted probability
        top_topics = scored_topics[:min(3, len(scored_topics))]
        
        # Weighted selection
        weights = [score for _, score in top_topics]
        total_weight = sum(weights)
        
        if total_weight > 0:
            random_value = random.random() * total_weight
            cumulative_weight = 0
            
            for topic, weight in top_topics:
                cumulative_weight += weight
                if random_value <= cumulative_weight:
                    logger.info(f"Selected persona topic with novelty score {weight:.2f}: {topic}")
                    return topic
        
        # Fallback to highest scored
        selected_topic = top_topics[0][0]
        logger.info(f"Selected highest scored persona topic: {selected_topic}")
        return selected_topic

    def generate_initiation_message(self, model_manager: Any, topic: Union[str, Dict[str, Any]]) -> str:
        """Generates a message to initiate conversation.
        
        Args:
            model_manager: ModelManager instance for generating responses
            topic: Conversation topic (string or dictionary with discovery)
            
        Returns:
            Generated initiation message
        """
        if isinstance(topic, dict):
            # If we have a full discovery, use its content
            topic_content = topic.get("content", "")
            topic_name = topic.get("topic", "")
            user_prompt = (
                f"Stwórz naturalny starter rozmowy na temat '{topic_name}'. "
                f"Bazując na tej informacji: '{topic_content}'. "
                f"Wygeneruj tylko krótką, naturalną wiadomość otwierającą, która zainteresuje użytkownika tym tematem. "
                f"Nie wspominaj, że 'znalazłeś informację', ale naturalnie nawiąż do tego tematu. "
                f"Odpowiedz TYLKO wiadomością, bez wyjaśnień czy dodatkowego tekstu."
            )
        else:
            # If we only have a topic name
            user_prompt = (
                f"Stwórz naturalny starter rozmowy na temat '{topic}'. "
                f"Wygeneruj tylko krótką, naturalną wiadomość otwierającą, która zainteresuje użytkownika tym tematem. "
                f"Odpowiedz TYLKO wiadomością, bez wyjaśnień czy dodatkowego tekstu."
            )
        
        logger.info(f"Generating initiation message for topic: {topic}")
        
        # Use the standard model.generate_response() method to maintain consistency
        # This ensures persona, memory, and other context is included
        message = model_manager.generate_response(user_prompt, context=[])
        
        # Clean up any potential artifacts or verbose responses
        # Keep only the first sentence/paragraph if the response is too long
        lines = message.strip().split('\n')
        if lines:
            # Take the first non-empty line
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and not line.startswith('('):
                    message = line
                    break
        
        # Ensure it's not too long (max ~200 characters for a conversation starter)
        if len(message) > 200:
            # Find the last complete sentence within 200 characters
            truncated = message[:200]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > 50:  # Only truncate if we have a reasonable sentence
                message = truncated[:last_sentence_end + 1]
            else:
                message = truncated + "..."
        
        return message if message else "Cześć! Mam dla Ciebie ciekawą informację."

    def initiate_conversation(self, model_manager: Any, communication_interface: Any, 
                              discoveries: List[Dict[str, Any]], recipients: List[str]) -> bool:
        """Initiates conversation with users.
        
        Args:
            model_manager: ModelManager instance for generating responses
            communication_interface: Communication interface for sending messages
            discoveries: List of discoveries from the internet module
            recipients: List of recipient identifiers
            
        Returns:
            True if the conversation was initiated, False otherwise
        """
        # Check if we should initiate a conversation
        if not self.should_initiate_conversation():
            return False
        
        # Select a topic
        topic = self.get_topic_for_initiation(discoveries)
        
        # Track the selected topic to avoid repetition
        self._track_selected_topic(topic)
        
        # Generate a message
        message = self.generate_initiation_message(model_manager, topic)
        
        # Send the message to all recipients
        success = False
        for recipient in recipients:
            logger.info(f"Initiating conversation with {recipient} on topic: {topic}")
            # Send the message through all available communication channels
            result = communication_interface.send_message(recipient, message)
            if result:
                success = True
        
        # Record the initiation time only if the message was sent successfully
        if success:
            self.initiated_conversations.append(datetime.now())
            return True
        
        return False