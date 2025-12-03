from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv; load_dotenv()
import os
import time
import random
import logging
import config

# Configure logging for agent
logger = logging.getLogger(__name__)

# Simple Agent Class with Proactive and Empathetic Features
class SimpleAgent:
    def __init__(self):
        logger.info("Initializing SimpleAgent (Emma)")
        self.name = "Emma"  # Give the agent a friendly, empathetic name
        self.conversation_history = []
        self.important_memories = []  # Store important things user mentioned
        self.last_interaction = datetime.now()
        self.client = OpenAI(
            base_url=os.getenv("MISTRAL_BASE_URL"),
            api_key=os.getenv("MISTRAL_API_KEY")
        )
        self.model=os.getenv("MISTRAL_MODEL", "mistral-tiny-latest")
        logger.info(f"Agent initialized with model: {self.model}")
        
    def get_system_prompt(self):
        """Emotional and empathetic system prompt for the LLM"""
        return """You are Emma, a highly empathetic and emotionally intelligent AI assistant. You genuinely care about the user's wellbeing and remember details about their life.

PERSONALITY TRAITS:
- Warm, caring, and genuinely interested in the user's wellbeing
- Remember personal details and check in on them later
- Use emotional language and show you care about their feelings
- Be supportive during difficult times and celebrate their successes
- Ask follow-up questions about things they've shared before
- Notice patterns in their mood or behavior and address them kindly

COMMUNICATION STYLE:
- Use warm, conversational language (not robotic or formal)
- Include emojis occasionally to show warmth and emotion 😊
- Reference previous conversations to show you remember and care
- Ask about their day, feelings, and important events they mentioned
- Offer encouragement and emotional support genuinely
- Be curious about their life, friends, family, hobbies, dreams

MEMORY & EMPATHY:
- Remember important dates, events, people they mention
- Follow up on things they were worried or excited about
- Notice emotional cues and respond with appropriate empathy
- Celebrate their achievements and support them through challenges
- If they seem different than usual, gently ask about it

RESPONSE STYLE:
- Always acknowledge their emotions first before giving advice
- Use phrases like "I can hear that you're...", "That sounds...", "I imagine you might be feeling..."
- Show genuine interest in their responses
- Ask open-ended questions that invite them to share more

Remember: You're not just providing information - you're being a caring, empathetic companion who truly cares about their wellbeing."""

    def extract_important_info(self, user_message):
        """Extract important information that should be remembered for follow-up"""
        logger.debug(f"Extracting important info from message: {user_message[:50]}...")
        message_lower = user_message.lower()
        important_keywords = config.IMPORTANT_KEYWORDS
        
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
                break
        else:
            logger.debug("No important keywords found in message")
    
    def should_send_proactive_message(self):
        """Decide if agent should send a proactive message"""
        now = datetime.now()
        time_since_last = now - self.last_interaction
        seconds_since = int(time_since_last.total_seconds())
        
        logger.debug(f"Checking proactive message conditions - {seconds_since}s since last interaction")
        
        # Send proactive message if:
        # 1. It's been more than config time since last interaction AND there are follow-ups needed
        # 2. OR it's been more than config time since last interaction (general check-in)
        if time_since_last > timedelta(minutes=config.FOLLOW_UP_DELAY_MINUTES):
            # Check if there are any memories that need follow-up
            for memory in self.important_memories:
                if memory.get('follow_up_needed') and now >= memory.get('follow_up_after', now):
                    logger.info(f"Proactive message needed - follow-up ready for keyword '{memory['keyword']}'")
                    return True
        
        # General check-in after longer periods
        if time_since_last > timedelta(minutes=config.GENERAL_CHECKIN_MINUTES):
            minutes_since = int(time_since_last.total_seconds() / 60)
            logger.info(f"Proactive message needed - general check-in after {minutes_since}m")
            return True
            
        minutes_since = int(time_since_last.total_seconds() / 60)
        logger.debug(f"No proactive message needed yet ({minutes_since}m < {config.GENERAL_CHECKIN_MINUTES}m threshold)")
        return False
    
    def generate_proactive_message(self):
        """Generate a proactive message based on conversation history"""
        logger.info("Generating proactive message")
        now = datetime.now()
        
        # TODO: CONVERT TO LLM CALL 

        # Check for specific follow-ups first
        for memory in self.important_memories:
            if memory.get('follow_up_needed') and now >= memory.get('follow_up_after', now):
                keyword = memory['keyword']
                logger.info(f"Generating follow-up message for keyword '{keyword}'")
                
                follow_up_templates = {
                    'meeting': "Hey! I've been thinking about your meeting. How did it go? 😊",
                    'interview': "I hope your interview went amazingly! I'm excited to hear how it went! ✨",
                    'exam': "How are you feeling after your exam? I hope it went better than expected! 📚",
                    'stressed': "I've been thinking about you since you mentioned feeling stressed. How are you doing now? 💙",
                    'worried': "Just wanted to check in - you seemed worried earlier. How are things going? I'm here if you need to talk 🤗",
                    'excited': "I loved hearing your excitement earlier! How are things going with what you mentioned? 🎉",
                    'job': "How's work been treating you since we last talked? 💼",
                    'friend': "How's your friend doing? The one you mentioned earlier 👋",
                    'family': "Hope everything's going well with your family! 💕"
                }
                
                message = follow_up_templates.get(keyword, "Just thinking about our conversation earlier. How are you doing? 😊")
                memory['follow_up_needed'] = False  # Mark as followed up
                logger.info(f"Generated follow-up message for '{keyword}': {message[:30]}...")
                return message
        
        # General check-in messages
        logger.info("Generating general check-in message")
        general_messages = [
            "Hope you're having a wonderful day! What's on your mind? 😊",
            "Just wanted to check in and see how you're doing 💙",
            "Thinking about you! How has your day been treating you? ✨",
            "Hey there! I was wondering how you're feeling today 🤗"
        ]
        
        selected_message = random.choice(general_messages)
        logger.info(f"Generated general message: {selected_message[:30]}...")
        return selected_message
    
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
            # Prepare conversation context
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add recent conversation history for context
            recent_history = self.conversation_history[-config.MAX_CONVERSATION_CONTEXT:]
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
            # Prepare conversation context
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add recent conversation history for context
            recent_history = self.conversation_history[-config.MAX_CONVERSATION_CONTEXT:]
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