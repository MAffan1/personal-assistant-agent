import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv; load_dotenv()
from simple_agent import SimpleAgent
import time
import threading
import logging
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Page setup - makes the webpage look nice
st.set_page_config(
    page_title="Simple WhatsApp Agent",
    page_icon="🤖"
)

# Initialize the agent - this runs once when the app starts
if 'agent' not in st.session_state:
    st.session_state.agent = SimpleAgent()
if 'messages' not in st.session_state:
    st.session_state.messages = []

@st.fragment(run_every=config.PROACTIVE_CHECK_FREQUENCY)  # Check for proactive messages
def check_proactive_messages():
    """Background fragment that automatically sends proactive messages"""
    logger.debug("Checking for proactive messages...")
    if st.session_state.agent.should_send_proactive_message():
        logger.info("Proactive message conditions met, generating message")
        proactive_message = st.session_state.agent.generate_proactive_message()
        logger.info(f"Generated proactive message: {proactive_message[:50]}...")
        st.session_state.messages.append({
            "sender": "agent", 
            "message": proactive_message, 
            "time": datetime.now().strftime("%H:%M:%S"),
            "proactive": True
        })
        # Reset the agent's last interaction to prevent immediate repeat
        st.session_state.agent.last_interaction = datetime.now()
        logger.info("Proactive message sent and interaction time reset")
        st.rerun()
    else:
        logger.debug("No proactive message needed")

def main():
    logger.info("Starting main application")
    # Title of the webpage
    st.title(f"💬 Chat with {st.session_state.agent.name}")
    st.write("An empathetic AI assistant who remembers and cares about you")
    
    # Run the automatic proactive message checker
    check_proactive_messages()
    
    # Show current time (this will update automatically)
    current_time = datetime.now().strftime('%H:%M:%S')
    st.markdown(f"🕒 **Current time:** {current_time}")
    
    # Create two columns - main chat area and sidebar
    col1, col2 = st.columns([3, 1])
    
    # Main chat area (left column)
    with col1:
        st.subheader("💬 Conversation")
        
        # Display all messages in the conversation
        for msg in st.session_state.messages:
            if msg["sender"] == "user":
                # Show user messages on the right
                st.chat_message("user").write(f"**You** ({msg['time']}): {msg['message']}")
            else:
                # Show agent messages on the left, with special indicator for proactive messages
                prefix = "🌟 **Emma** (proactive)" if msg.get('proactive') else f"**{st.session_state.agent.name}**"
                st.chat_message("assistant").write(f"{prefix} ({msg['time']}): {msg['message']}")
        
        # Input box for user to type messages
        user_input = st.chat_input("Share what's on your mind...")
        
        # When user sends a message
        if user_input:
            logger.info(f"User input received: {user_input[:50]}...")
            # Update last interaction time and extract important info
            st.session_state.agent.last_interaction = datetime.now()
            st.session_state.agent.extract_important_info(user_input)
            logger.debug(f"Important info extracted, memories count: {len(st.session_state.agent.important_memories)}")
            
            # Add user message to display immediately
            st.session_state.messages.append({
                "sender": "user", 
                "message": user_input, 
                "time": datetime.now().strftime("%H:%M:%S")
            })
            logger.debug("User message added to display messages")
            
            # Add user message to conversation history
            st.session_state.agent.conversation_history.append({
                "sender": "user", 
                "message": user_input, 
                "time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now()
            })
            
            # Show user message immediately
            with st.chat_message("user"):
                st.write(f"**You** ({datetime.now().strftime('%H:%M:%S')}): {user_input}")
            
            # Create placeholder for streaming response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Get streaming response
                logger.info("Starting LLM streaming response generation")
                stream = st.session_state.agent.generate_llm_response_stream(user_input)
                
                # Process the stream
                try:
                    chunk_count = 0
                    for chunk in stream:
                        chunk_count += 1
                        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                                content = chunk.choices[0].delta.content
                                if content:
                                    full_response += content
                                    # Update the message placeholder with current response
                                    message_placeholder.write(f"**{st.session_state.agent.name}** ({datetime.now().strftime('%H:%M:%S')}): {full_response}▋")
                    logger.info(f"Streaming completed with {chunk_count} chunks, response length: {len(full_response)}")
                except Exception as e:
                    logger.error(f"Streaming failed: {str(e)}, falling back to regular response")
                    # If streaming fails, fall back to regular response
                    full_response = st.session_state.agent.generate_llm_response(user_input)
                
                # Final update without cursor
                message_placeholder.write(f"**{st.session_state.agent.name}** ({datetime.now().strftime('%H:%M:%S')}): {full_response}")
            
            # Save agent response to history
            agent_time = datetime.now().strftime("%H:%M:%S")
            st.session_state.agent.conversation_history.append({
                "sender": "agent", 
                "message": full_response, 
                "time": agent_time,
                "timestamp": datetime.now()
            })
            
            # Add agent response to display messages
            st.session_state.messages.append({
                "sender": "agent", 
                "message": full_response, 
                "time": agent_time
            })
            
            # Refresh to show the new conversation
            st.rerun()
    
    # Sidebar (right column)
    with col2:
        st.subheader("🧠 Emma's Memory")
        
        # Show agent info
        st.write(f"**Agent:** {st.session_state.agent.name}")
        st.write("*Empathetic AI Assistant*")
        
        # Show conversation stats
        total_messages = len(st.session_state.messages)
        st.write(f"**Messages:** {total_messages}")
        
        # Show important memories
        if st.session_state.agent.important_memories:
            st.subheader("💭 What I Remember")
            recent_memories = st.session_state.agent.important_memories[-config.MAX_MEMORIES_DISPLAYED:]
            for memory in recent_memories:
                keyword = memory['keyword']
                time_ago = datetime.now() - memory['timestamp']
                hours_ago = int(time_ago.total_seconds() / 3600)
                
                with st.expander(f"🔖 {keyword.title()} ({hours_ago}h ago)"):
                    st.write(memory['content'][:100] + "..." if len(memory['content']) > 100 else memory['content'])
                    if memory.get('follow_up_needed'):
                        st.write("💡 *Will follow up on this*")
        
        st.markdown("---")
        
        # Proactive messaging controls
        st.subheader("🌟 Proactive Features")
        
        # Status display (updates less frequently to avoid UI dimming)
        @st.fragment(run_every=config.STATUS_UPDATE_FREQUENCY)  # Update frequency from config
        def show_live_status():
            time_since = datetime.now() - st.session_state.agent.last_interaction
            minutes_ago = int(time_since.total_seconds() / 60)
            seconds_ago = int(time_since.total_seconds() % 60)
            st.write(f"**Last interaction:** {minutes_ago}m {seconds_ago}s ago")
            
            if st.session_state.agent.should_send_proactive_message():
                st.write("🔔 **Proactive message ready!**")
            else:
                # Show countdown using config timing
                remaining_seconds = (config.GENERAL_CHECKIN_MINUTES * 60) - int(time_since.total_seconds())
                if remaining_seconds > 0:
                    remaining_minutes = remaining_seconds // 60
                    remaining_secs = remaining_seconds % 60
                    if remaining_minutes > 0:
                        st.write(f"⏰ Next check-in in {remaining_minutes}m {remaining_secs}s")
                    else:
                        st.write(f"⏰ Next check-in in {remaining_secs}s")
                else:
                    st.write("⏰ Ready for check-in")
        
        show_live_status()
        
        # Manual controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Check Now"):
                logger.info("Manual proactive check triggered")
                if st.session_state.agent.should_send_proactive_message():
                    logger.info("Manual check: proactive message conditions met")
                    check_proactive_messages()
                else:
                    logger.info("Manual check: no proactive message needed")
                    st.info("No proactive message needed yet")
        with col2:
            if st.button("💌 Force Send"):
                logger.info("Force send proactive message triggered")
                proactive_msg = st.session_state.agent.generate_proactive_message()
                logger.info(f"Force sent proactive message: {proactive_msg[:50]}...")
                st.session_state.messages.append({
                    "sender": "agent", 
                    "message": proactive_msg, 
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "proactive": True
                })
                # Reset last interaction to prevent immediate repeat
                st.session_state.agent.last_interaction = datetime.now()
                st.rerun()
        

        
        st.markdown("---")
        
        # Settings and controls
        st.subheader("⚙️ Controls")
        
        # Button to clear chat
        if st.button("🗑️ Clear Chat"):
            logger.info(f"Clearing chat - had {len(st.session_state.messages)} messages, {len(st.session_state.agent.important_memories)} memories")
            st.session_state.messages = []
            st.session_state.agent.conversation_history = []
            st.session_state.agent.important_memories = []
            logger.info("Chat cleared successfully")
            st.rerun()
        
        # Show system prompt
        with st.expander("📋 View System Prompt"):
            st.text_area("Emma's Instructions:", st.session_state.agent.get_system_prompt(), height=200, disabled=True)

# Run the main function
if __name__ == "__main__":
    main()