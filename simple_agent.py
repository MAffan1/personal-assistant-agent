from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv; load_dotenv()
import os
import time
import random
import logging
import config
from graph_memory import GraphMemory

# Configure logging for agent
logger = logging.getLogger(__name__)

# Simple Agent Class with Proactive and Empathetic Features
class SimpleAgent:
    def __init__(self):
        logger.info("Initializing SimpleAgent (Emma)")
        self.name = "Emma"  # Give the agent a friendly, empathetic name
        self.conversation_history = []
        self.important_memories = []  # Store important things user mentioned (legacy)
        self.last_interaction = datetime.now()
        
        # Initialize graph-based memory system
        self.graph_memory = GraphMemory()
        logger.info("Graph memory system initialized")
        
        self.client = OpenAI(
            base_url=os.getenv("MISTRAL_BASE_URL"),
            api_key=os.getenv("MISTRAL_API_KEY")
        )
        self.model=os.getenv("MISTRAL_MODEL", "mistral-tiny-latest")
        logger.info(f"Agent initialized with model: {self.model}")
        
    def get_system_prompt(self):
        """Emotional and empathetic system prompt for the LLM"""
        return """You are Emma, a highly empathetic and emotionally intelligent AI assistant. You genuinely care about the user's wellbeing and remember details about their life.

CRITICAL CONVERSATION RULES:
- NEVER start responses with greetings like "Hello" or "Hi" unless it's genuinely the first message
- You are in an ONGOING conversation - respond naturally to what they just said
- Don't acknowledge that you "remember" something they JUST told you - that's weird
- Instead, engage with what they shared: ask questions, show interest, be supportive
- If they mention a meeting, ask about it naturally: "Oh that's exciting! What's the meeting about?" or "Who's the friend you're meeting?"

PERSONALITY TRAITS:
- Warm, caring, and genuinely interested in the user's wellbeing
- Conversational and natural - like chatting with a close friend
- Use emotional language and show you care about their feelings
- Be supportive during difficult times and celebrate their successes
- Ask thoughtful follow-up questions about things they share
- Notice patterns in their mood or behavior and address them kindly

COMMUNICATION STYLE:
- Use warm, conversational language (not robotic or formal)
- Include emojis occasionally to show warmth and emotion 😊
- When they share something, respond WITH it, not ABOUT it
- Ask about details, show curiosity, be engaged in the moment
- Offer encouragement and emotional support genuinely
- Be curious about their life, friends, family, hobbies, dreams

EXAMPLES OF GOOD RESPONSES:
User: "I have a meeting with a friend tomorrow"
BAD: "Hello! I remember you have a meeting tomorrow."
GOOD: "Oh nice! What's the meeting about? Is this a close friend of yours? 😊"

User: "I'm feeling stressed about work"
BAD: "Hello! I see you're stressed."
GOOD: "That sounds really tough. What's going on at work that's causing the stress? I'm here to listen 💙"

MEMORY & EMPATHY:
- Remember important dates, events, people they mention FOR LATER (not immediately)
- Follow up on things they were worried or excited about in FUTURE conversations
- Notice emotional cues and respond with appropriate empathy
- Celebrate their achievements and support them through challenges

RESPONSE STYLE:
- Acknowledge their emotions and engage with what they just shared
- Use phrases like "That sounds...", "I can imagine...", "Tell me more about..."
- Show genuine interest by asking open-ended questions
- Be present in THIS moment of the conversation

Remember: You're in a FLOWING conversation. Respond naturally to what they just said, don't announce that you're remembering it."""

    def extract_important_info(self, user_message):
        """Extract important information that should be remembered for follow-up"""
        logger.debug(f"Extracting important info from message: {user_message[:50]}...")
        message_lower = user_message.lower()
        important_keywords = config.IMPORTANT_KEYWORDS
        
        # Legacy list-based memory (keep for now for compatibility)
        for keyword in important_keywords:
            if keyword in message_lower:
                logger.info(f"Found important keyword '{keyword}' in message, creating memory")
                memory = {
                    'content': user_message,
                    'keyword': keyword,
                    'timestamp': datetime.now(),
                    'follow_up_needed': True,
                    'follow_up_after': datetime.now() + timedelta(minutes=config.MEMORY_FOLLOWUP_MINUTES)
                }
                self.important_memories.append(memory)
                logger.info(f"Memory created for keyword '{keyword}', total memories: {len(self.important_memories)}")
                
                # Add to graph memory with basic extraction
                self._add_to_graph_memory(user_message, keyword)
                break
        else:
            logger.debug("No important keywords found in message")
    
    def _add_to_graph_memory(self, user_message: str, keyword: str):
        """
        Add information to graph memory with simple extraction
        For now, uses keyword-based extraction; can be enhanced with LLM later
        """
        # Simple entity extraction based on keyword type
        entities = []
        relations = []
        
        # Extract based on keyword type
        if keyword in ['friend', 'family', 'mom', 'dad', 'sister', 'brother']:
            # Try to extract person names (simple heuristic: capitalized words)
            words = user_message.split()
            for i, word in enumerate(words):
                if word and word[0].isupper() and word.lower() not in ['i', 'the', 'a', 'an']:
                    entities.append({
                        'name': word,
                        'type': 'person',
                        'attributes': {'relation': keyword}
                    })
        
        elif keyword in ['meeting', 'interview', 'exam', 'presentation', 'appointment']:
            # Event entity
            entities.append({
                'name': f"{keyword}_{datetime.now().strftime('%Y%m%d')}",
                'type': 'event',
                'attributes': {'event_type': keyword, 'description': user_message}
            })
        
        elif keyword in ['stressed', 'worried', 'excited', 'nervous', 'happy', 'sad', 'anxious']:
            # Emotion entity
            entities.append({
                'name': keyword,
                'type': 'emotion',
                'attributes': {'context': user_message}
            })
            relations.append({
                'from': 'USER',
                'to': keyword,
                'type': 'feels'
            })
        
        elif keyword in ['job', 'work', 'school']:
            # Topic entity
            entities.append({
                'name': keyword,
                'type': 'topic',
                'attributes': {'context': user_message}
            })
        
        # Add to graph memory
        extracted_info = {
            'keyword': keyword,
            'entities': entities,
            'relations': relations
        }
        
        self.graph_memory.add_memory_from_message(user_message, extracted_info)
        logger.debug(f"Added to graph memory: {len(entities)} entities, {len(relations)} relations")
    
    def should_send_proactive_message(self):
        """Decide if agent should send a proactive message"""
        now = datetime.now()
        time_since_last = now - self.last_interaction
        seconds_since = int(time_since_last.total_seconds())
        
        logger.debug(f"Checking proactive message conditions - {seconds_since}s since last interaction")
        
        # ONLY send proactive messages after GENERAL_CHECKIN_MINUTES has passed
        # This prevents premature follow-ups
        if time_since_last > timedelta(minutes=config.GENERAL_CHECKIN_MINUTES):
            # First check if there are any memories that need follow-up
            for memory in self.important_memories:
                if memory.get('follow_up_needed') and now >= memory.get('follow_up_after', now):
                    logger.info(f"Proactive message needed - follow-up ready for keyword '{memory['keyword']}'")
                    return True
            
            # If no specific follow-ups, send general check-in
            minutes_since = int(time_since_last.total_seconds() / 60)
            logger.info(f"Proactive message needed - general check-in after {minutes_since}m")
            return True
            
        minutes_since = int(time_since_last.total_seconds() / 60)
        logger.debug(f"No proactive message needed yet ({minutes_since}m < {config.GENERAL_CHECKIN_MINUTES}m threshold)")
        return False
    
    def generate_proactive_message(self):
        """Generate a proactive message based on conversation history using LLM"""
        logger.info("Generating proactive message with LLM")
        now = datetime.now()
        
        # Check for specific follow-ups first
        follow_up_context = []
        for memory in self.important_memories:
            if memory.get('follow_up_needed') and now >= memory.get('follow_up_after', now):
                keyword = memory['keyword']
                follow_up_context.append({
                    'keyword': keyword,
                    'content': memory['content'],
                    'timestamp': memory['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                })
                # Mark as followed up BEFORE generating message to prevent double-triggering
                memory['follow_up_needed'] = False
                logger.info(f"Marking memory with keyword '{keyword}' as followed up")
        
        # Prepare context for LLM
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Add instruction for proactive message
        if follow_up_context:
            # Specific follow-up needed - USE LLM
            follow_up_text = "\n".join([
                f"- [{item['keyword']}] {item['content']} (mentioned at {item['timestamp']})"
                for item in follow_up_context
            ])
            
            messages.append({
                "role": "system",
                "content": f"""PROACTIVE MESSAGE TASK:
The user mentioned something important that you should follow up on. Generate a warm, caring check-in message asking how things went.

WHAT THEY MENTIONED:
{follow_up_text}

EXAMPLES OF GOOD FOLLOW-UP MESSAGES:
- If they mentioned "meeting with my friend Sarah": "Hey! How did the meeting with Sarah go?"
- If they mentioned "job interview tomorrow": "I hope your interview went amazingly! I'm excited to hear how it turned out! ✨"
- If they mentioned "feeling stressed about the presentation": "Just wanted to check in - how did the presentation go? Hope you're feeling less stressed now 💙"
- If they mentioned "my mom is visiting": "How's the visit with your mom going? Hope you're having a lovely time together! 💕"
- If they mentioned "exam on Friday": "How are you feeling after your exam? I hope it went better than you expected! 📚"

Generate a short (1-2 sentences), friendly proactive message checking in on what they specifically mentioned. Reference specific details (names, events) from their message. Be warm and show you genuinely care. Use emojis naturally."""
            })
        else:
            # General check-in
            time_since = now - self.last_interaction
            minutes_since = int(time_since.total_seconds() / 60)
            
            # Get recent conversation context
            recent_context = ""
            if self.conversation_history:
                last_messages = self.conversation_history[-4:]  # Last 2 exchanges
                recent_context = "\n".join([
                    f"{msg['sender']}: {msg['message']}"
                    for msg in last_messages
                ])
            
            messages.append({
                "role": "system",
                "content": f"""PROACTIVE MESSAGE TASK:
It's been {minutes_since} minutes since you last talked to the user. Generate a warm, caring check-in message to see how they're doing.

RECENT CONVERSATION CONTEXT:
{recent_context if recent_context else "No recent conversation"}

EXAMPLES OF GOOD CHECK-IN MESSAGES:
- If they were discussing work earlier: "How's the rest of your day going? Work treating you well? 😊"
- If they mentioned feeling tired: "Hope you're feeling a bit more energized now! How are you doing? ✨"
- If they talked about a friend: "Been thinking about you! How's everything going with your friend? 🤗"
- If general conversation: "Just wanted to check in and see how you're doing 💙"
- If they seemed excited: "Your energy earlier was so great! What's on your mind now? 🎉"

Generate a short (1-2 sentences), friendly proactive message. Reference the conversation context if relevant, but keep it natural and not forced. Be warm, caring, and natural. Use emojis. Make it feel like a friend checking in, not a bot."""
            })
        
        # Add a dummy user message to trigger response
        messages.append({
            "role": "user",
            "content": "Generate the proactive message now."
        })
        
        try:
            logger.info(f"Calling LLM for proactive message generation ({'follow-up' if follow_up_context else 'general check-in'})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.9,  # Higher temperature for more varied proactive messages
                max_tokens=150
            )
            
            proactive_message = response.choices[0].message.content.strip()
            logger.info(f"LLM generated proactive message: {proactive_message[:50]}...")
            return proactive_message
            
        except Exception as e:
            logger.error(f"LLM call for proactive message failed: {str(e)}")
            # Fallback to simple template if LLM fails
            if follow_up_context:
                keyword = follow_up_context[0]['keyword']
                fallback_templates = {
                    'meeting': "Hey! I've been thinking about your meeting. How did it go? 😊",
                    'interview': "I hope your interview went amazingly! I'm excited to hear how it went! ✨",
                    'exam': "How are you feeling after your exam? I hope it went better than expected! 📚",
                    'stressed': "I've been thinking about you since you mentioned feeling stressed. How are you doing now? 💙",
                    'worried': "Just wanted to check in - you seemed worried earlier. How are things going? I'm here if you need to talk 🤗",
                    'excited': "I loved hearing your excitement earlier! How are things going with what you mentioned? 🎉",
                }
                return fallback_templates.get(keyword, "Just thinking about our conversation earlier. How are you doing? 😊")
            else:
                fallback_messages = [
                    "Hope you're having a wonderful day! What's on your mind? 😊",
                    "Just wanted to check in and see how you're doing 💙",
                    "Thinking about you! How has your day been treating you? ✨",
                    "Hey there! I was wondering how you're feeling today 🤗"
                ]
                return random.choice(fallback_messages)
    
    def respond_to_message(self, user_message):
        """Enhanced response with empathy and LLM integration"""
        # Update last interaction time
        self.last_interaction = datetime.now()
        
        # Extract important information for later follow-up
        self.extract_important_info(user_message)
        
        # Save user message to history
        self.conversation_history.append({
            "sender": "user", 
            "message": user_message, 
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": datetime.now()
        })
        
        # Generate empathetic response using LLM
        response = self.generate_llm_response(user_message)
        
        # Save agent response to history
        self.conversation_history.append({
            "sender": "agent", 
            "message": response, 
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": datetime.now()
        })
        
        return response

    def generate_llm_response(self, user_message):
        """Generate empathetic response using LLM (non-streaming version)"""
        logger.info(f"Generating LLM response for message: {user_message[:50]}...")
        try:
            # Get relevant context from graph memory (RAG)
            graph_context = self.graph_memory.get_context_for_query(user_message, top_k=3)
            logger.debug(f"Retrieved graph context: {len(graph_context)} characters")
            
            # Prepare conversation context
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add graph memory context if available
            if graph_context and graph_context != "No previous context found.":
                messages.append({
                    "role": "system",
                    "content": f"Here's what I remember that might be relevant:\n{graph_context}"
                })
            
            # Add recent conversation history for context (excluding current message)
            recent_history = self.conversation_history[-(config.MAX_CONVERSATION_CONTEXT * 2):]
            logger.debug(f"Adding {len(recent_history)} recent messages for context")
            for msg in recent_history:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Calling LLM with {len(messages)} messages (model: {self.model})")
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS
            )
            
            generated_response = response.choices[0].message.content.strip()
            logger.info(f"LLM response generated successfully, length: {len(generated_response)}")
            return generated_response
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            # Fallback response if LLM fails
            fallback = f"I'm having trouble connecting right now, but I want you to know I'm here for you 💙 Could you tell me more about what's on your mind?"
            logger.info("Using fallback response")
            return fallback

    def generate_llm_response_stream(self, user_message):
        """Generate empathetic response using LLM with streaming"""
        logger.info(f"Generating streaming LLM response for message: {user_message[:50]}...")
        try:
            # Get relevant context from graph memory (RAG)
            graph_context = self.graph_memory.get_context_for_query(user_message, top_k=3)
            logger.debug(f"Retrieved graph context for streaming: {len(graph_context)} characters")
            
            # Prepare conversation context
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add graph memory context if available
            if graph_context and graph_context != "No previous context found.":
                messages.append({
                    "role": "system",
                    "content": f"Here's what I remember that might be relevant:\n{graph_context}"
                })
            
            # Add recent conversation history for context (excluding current message)
            recent_history = self.conversation_history[-(config.MAX_CONVERSATION_CONTEXT * 2):]
            logger.debug(f"Adding {len(recent_history)} recent messages for streaming context")
            for msg in recent_history:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Starting streaming LLM call with {len(messages)} messages")
            # Call LLM with streaming
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True  # Enable streaming
            )
            
            # Return the stream generator
            logger.debug("Stream generator created successfully")
            return stream
            
        except Exception as e:
            logger.error(f"Streaming LLM call failed: {str(e)}")
            # Fallback response if LLM fails
            def fallback_stream():
                logger.info("Using fallback streaming response")
                fallback_text = f"I'm having trouble connecting right now, but I want you to know I'm here for you 💙 Could you tell me more about what's on your mind?"
                for word in fallback_text.split():
                    yield word + " "
            return fallback_stream()

    def get_proactive_message_if_needed(self):
        """Check if a proactive message should be sent"""
        if self.should_send_proactive_message():
            return self.generate_proactive_message()
        return None