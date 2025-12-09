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
if 'show_live_graph' not in st.session_state:
    st.session_state.show_live_graph = False
if 'graph_node_count' not in st.session_state:
    st.session_state.graph_node_count = 0

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
    st.title(f"💬 {st.session_state.agent.name} - Your Empathetic AI Companion")
    
    # Run the automatic proactive message checker
    check_proactive_messages()
    
    # Top horizontal bar with status and quick controls
    col_time, col_status, col_clear = st.columns([2, 3, 1])
    
    with col_time:
        current_time = datetime.now().strftime('%H:%M:%S')
        st.markdown(f"🕒 **{current_time}**")
    
    with col_status:
        time_since = datetime.now() - st.session_state.agent.last_interaction
        minutes_ago = int(time_since.total_seconds() / 60)
        seconds_ago = int(time_since.total_seconds() % 60)
        
        if st.session_state.agent.should_send_proactive_message():
            st.markdown("🔔 **Proactive message ready!**")
        else:
            st.markdown(f"💬 Last chat: **{minutes_ago}m {seconds_ago}s ago**")
    
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            logger.info(f"Clearing chat - had {len(st.session_state.messages)} messages")
            st.session_state.messages = []
            st.session_state.agent.conversation_history = []
            st.session_state.agent.important_memories = []
            logger.info("Chat cleared successfully")
            st.rerun()
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🕸️ Knowledge Graph", "🧠 Memory & Settings"])
    
    # TAB 1: CHAT INTERFACE
    with tab1:
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
    
    # TAB 2: KNOWLEDGE GRAPH VISUALIZATION
    with tab2:
        st.subheader("🕸️ Your Knowledge Graph")
        st.write("Interactive visualization of everything Emma remembers about you")
        
        # Graph statistics at the top
        graph_stats = st.session_state.agent.graph_memory.get_graph_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Memories", graph_stats['total_memories'])
        with col2:
            st.metric("Entities", graph_stats['total_nodes'])
        with col3:
            st.metric("Connections", graph_stats['total_edges'])
        with col4:
            people_count = graph_stats['entities_by_type'].get('person', 0)
            st.metric("People", people_count)
        
        st.markdown("---")
        
        # Live graph visualization toggle
        show_live = st.checkbox(
            "🔄 Auto-refresh graph (updates every 5 seconds)",
            value=st.session_state.show_live_graph,
            help="Automatically update the graph as new memories are added"
        )
        st.session_state.show_live_graph = show_live
        
        if st.session_state.show_live_graph:
            # Live updating graph fragment
            @st.fragment(run_every=5)
            def show_live_graph():
                current_count = st.session_state.agent.graph_memory.graph.number_of_nodes()
                
                # Only regenerate if graph changed
                if current_count != st.session_state.graph_node_count:
                    st.session_state.graph_node_count = current_count
                    logger.info(f"Graph changed ({current_count} nodes), regenerating visualization")
                
                try:
                    html_content = st.session_state.agent.graph_memory.visualize_graph()
                    if html_content:
                        # Display the visualization in full width
                        st.components.v1.html(html_content, height=700, scrolling=True)
                        
                        # Legend below
                        st.caption("**Legend:** 🌟 User | 🔵 Person | 🟩 Event | 🔺 Emotion | 🔷 Topic | 📦 Memory")
                        st.caption(f"💡 **Tip:** Zoom with scroll wheel, drag nodes to rearrange, hover for details | **Nodes:** {current_count}")
                except ImportError:
                    st.warning("⚠️ pyvis not installed. Showing simple visualization...")
                    fig = st.session_state.agent.graph_memory.create_simple_visualization()
                    if fig:
                        st.pyplot(fig, use_container_width=True)
                    else:
                        st.error("Please install: `pip install pyvis matplotlib`")
                except Exception as e:
                    logger.error(f"Error visualizing graph: {e}")
                    st.error(f"Error generating visualization: {e}")
            
            show_live_graph()
        else:
            # Manual refresh button
            if st.button("🔍 Generate Graph Visualization", use_container_width=True, type="primary"):
                with st.spinner("Generating interactive graph..."):
                    try:
                        html_content = st.session_state.agent.graph_memory.visualize_graph()
                        if html_content:
                            st.components.v1.html(html_content, height=700, scrolling=True)
                            st.caption("**Legend:** 🌟 User | 🔵 Person | 🟩 Event | 🔺 Emotion | 🔷 Topic | 📦 Memory")
                            st.caption("💡 **Tip:** Zoom with scroll wheel, drag nodes to rearrange, hover for details")
                    except ImportError:
                        st.warning("⚠️ pyvis not installed. Showing simple visualization...")
                        fig = st.session_state.agent.graph_memory.create_simple_visualization()
                        if fig:
                            st.pyplot(fig, use_container_width=True)
                        else:
                            st.error("Please install: `pip install pyvis matplotlib`")
                    except Exception as e:
                        logger.error(f"Error visualizing graph: {e}")
                        st.error(f"Error: {e}")
            else:
                st.info("👆 Click the button above to visualize your knowledge graph, or enable auto-refresh")
        
        # Entity breakdown
        st.markdown("---")
        st.subheader("📊 Entity Breakdown")
        
        entity_cols = st.columns(3)
        entity_types = list(graph_stats['entities_by_type'].items())
        
        for idx, (entity_type, count) in enumerate(entity_types):
            if entity_type != 'user':  # Don't show user node
                with entity_cols[idx % 3]:
                    st.metric(f"{entity_type.title()}s", count)
    
    # TAB 3: MEMORY & SETTINGS
    with tab3:
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("💭 Recent Memories")
            
            if st.session_state.agent.important_memories:
                recent_memories = st.session_state.agent.important_memories[-10:][::-1]  # Last 10, reversed
                for memory in recent_memories:
                    keyword = memory['keyword']
                    time_ago = datetime.now() - memory['timestamp']
                    hours_ago = int(time_ago.total_seconds() / 3600)
                    minutes_ago = int((time_ago.total_seconds() % 3600) / 60)
                    
                    time_str = f"{hours_ago}h ago" if hours_ago > 0 else f"{minutes_ago}m ago"
                    
                    with st.expander(f"🔖 {keyword.title()} • {time_str}"):
                        st.write(memory['content'])
                        if memory.get('follow_up_needed'):
                            st.write("💡 *Will follow up on this*")
            else:
                st.info("No memories yet. Start chatting with Emma!")
        
        with col_right:
            st.subheader("🌟 Proactive Settings")
            
            # Live status
            @st.fragment(run_every=5)
            def show_status():
                time_since = datetime.now() - st.session_state.agent.last_interaction
                minutes_ago = int(time_since.total_seconds() / 60)
                seconds_ago = int(time_since.total_seconds() % 60)
                
                st.metric("Time Since Last Chat", f"{minutes_ago}m {seconds_ago}s")
                
                if st.session_state.agent.should_send_proactive_message():
                    st.success("🔔 Proactive message ready!")
                else:
                    remaining_seconds = (config.GENERAL_CHECKIN_MINUTES * 60) - int(time_since.total_seconds())
                    if remaining_seconds > 0:
                        remaining_minutes = remaining_seconds // 60
                        remaining_secs = remaining_seconds % 60
                        st.info(f"⏰ Next check-in in {remaining_minutes}m {remaining_secs}s")
            
            show_status()
            
            st.markdown("---")
            
            # Manual controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Check Now", use_container_width=True):
                    if st.session_state.agent.should_send_proactive_message():
                        check_proactive_messages()
                    else:
                        st.info("No proactive message needed yet")
            
            with col2:
                if st.button("💌 Force Send", use_container_width=True):
                    proactive_msg = st.session_state.agent.generate_proactive_message()
                    st.session_state.messages.append({
                        "sender": "agent", 
                        "message": proactive_msg, 
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "proactive": True
                    })
                    st.session_state.agent.last_interaction = datetime.now()
                    st.rerun()
            
            st.markdown("---")
            st.subheader("⚙️ Configuration")
            
            with st.expander("📋 View System Prompt"):
                st.text_area(
                    "Emma's Instructions:", 
                    st.session_state.agent.get_system_prompt(), 
                    height=300, 
                    disabled=True
                )
            
            with st.expander("📊 Statistics"):
                total_messages = len(st.session_state.messages)
                user_messages = len([m for m in st.session_state.messages if m["sender"] == "user"])
                agent_messages = len([m for m in st.session_state.messages if m["sender"] == "agent"])
                
                st.write(f"**Total Messages:** {total_messages}")
                st.write(f"**Your Messages:** {user_messages}")
                st.write(f"**Emma's Responses:** {agent_messages}")
                st.write(f"**Memories Stored:** {len(st.session_state.agent.important_memories)}")

# Run the main function
if __name__ == "__main__":
    main()