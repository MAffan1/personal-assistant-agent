from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv; load_dotenv()
import os
import time
import random

# Simple Agent Class with Proactive and Empathetic Features
class SimpleAgent:
    def __init__(self):
        self.name = "Emma"  # Give the agent a friendly, empathetic name
        self.conversation_history = []
        self.important_memories = []  # Store important things user mentioned
        self.last_interaction = datetime.now()
        self.client = OpenAI(
            base_url=os.getenv("MISTRAL_BASE_URL"),
            api_key=os.getenv("MISTRAL_API_KEY")
        )
        self.model=os.getenv("MISTRAL_MODEL", "mistral-tiny-latest")
        
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
        message_lower = user_message.lower()
        important_keywords = [
            # Events and appointments
            'meeting', 'appointment', 'interview', 'date', 'deadline', 'exam', 'test', 'presentation',
            # People and relationships  
            'friend', 'family', 'mom', 'dad', 'sister', 'brother', 'boyfriend', 'girlfriend', 'partner',
            # Emotions and states
            'stressed', 'worried', 'excited', 'nervous', 'happy', 'sad', 'anxious', 'tired', 'overwhelmed',
            # Important activities
            'job', 'work', 'school', 'vacation', 'trip', 'birthday', 'anniversary', 'graduation',
            # Health and wellbeing
            'doctor', 'sick', 'medicine', 'exercise', 'diet', 'sleep', 'therapy'
        ]
        
        for keyword in important_keywords:
            if keyword in message_lower:
                memory = {
                    'content': user_message,
                    'keyword': keyword,
                    'timestamp': datetime.now(),
                    'follow_up_needed': True,
                    'follow_up_after': datetime.now() + timedelta(seconds=15)  # Follow up after 15 seconds for testing
                }
                self.important_memories.append(memory)
                break
    
    def should_send_proactive_message(self):
        """Decide if agent should send a proactive message"""
        now = datetime.now()
        time_since_last = now - self.last_interaction
        
        # Send proactive message if:
        # 1. It's been more than 10 seconds since last interaction AND there are follow-ups needed
        # 2. OR it's been more than 20 seconds since last interaction (general check-in)
        if time_since_last > timedelta(seconds=10):
            # Check if there are any memories that need follow-up
            for memory in self.important_memories:
                if memory.get('follow_up_needed') and now >= memory.get('follow_up_after', now):
                    return True
        
        # General check-in after longer periods (reduced to seconds for testing)
        if time_since_last > timedelta(seconds=20):
            return True
            
        return False
    
    def generate_proactive_message(self):
        """Generate a proactive message based on conversation history"""
        now = datetime.now()
        
        # TODO: CONVERT TO LLM CALL 

        # Check for specific follow-ups first
        for memory in self.important_memories:
            if memory.get('follow_up_needed') and now >= memory.get('follow_up_after', now):
                keyword = memory['keyword']
                
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
                return message
        
        # General check-in messages
        general_messages = [
            "Hope you're having a wonderful day! What's on your mind? 😊",
            "Just wanted to check in and see how you're doing 💙",
            "Thinking about you! How has your day been treating you? ✨",
            "Hey there! I was wondering how you're feeling today 🤗"
        ]
        
        return random.choice(general_messages)
    
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
        try:
            # Prepare conversation context
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add recent conversation history for context
            recent_history = self.conversation_history[-6:]  # Last 6 messages
            for msg in recent_history:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,  # Higher temperature for more empathetic, varied responses
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback response if LLM fails
            return f"I'm having trouble connecting right now, but I want you to know I'm here for you 💙 Could you tell me more about what's on your mind?"

    def generate_llm_response_stream(self, user_message):
        """Generate empathetic response using LLM with streaming"""
        try:
            # Prepare conversation context
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add recent conversation history for context
            recent_history = self.conversation_history[-6:]  # Last 6 messages
            for msg in recent_history:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call LLM with streaming
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=300,
                stream=True  # Enable streaming
            )
            
            # Return the stream generator
            return stream
            
        except Exception as e:
            # Fallback response if LLM fails
            def fallback_stream():
                fallback_text = f"I'm having trouble connecting right now, but I want you to know I'm here for you 💙 Could you tell me more about what's on your mind?"
                for word in fallback_text.split():
                    yield word + " "
            return fallback_stream()

    def get_proactive_message_if_needed(self):
        """Check if a proactive message should be sent"""
        if self.should_send_proactive_message():
            return self.generate_proactive_message()
        return None