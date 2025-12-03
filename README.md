# Personal Assistant AI Agent

A simple, empathetic AI assistant built with Streamlit that remembers conversations and proactively engages with users.

## 🚀 Features

### Emma - Your Empathetic AI Assistant

- **🧠 Memory System**: Remembers important details about your life, relationships, and events
- **💙 Empathetic Responses**: Genuinely cares about your wellbeing with warm, emotional communication
- **🌟 Proactive Engagement**: Automatically follows up on important things you mention
- **💬 Streaming Responses**: Real-time conversation with live response generation
- **⏰ Smart Check-ins**: Reaches out after periods of inactivity to see how you're doing
- **📝 Conversation History**: Maintains context across multiple interactions

### Key Capabilities

- **Emotional Intelligence**: Recognizes and responds to your emotional state
- **Follow-up System**: Remembers meetings, interviews, concerns, and follows up later
- **Natural Conversations**: Chat-based interface with immediate message display
- **Memory Persistence**: Stores important memories and references them in future conversations
- **Live Status Tracking**: Shows real-time interaction timing and proactive message status

## 🏗️ Architecture

```
personal-assistant/
├── app.py              # Main Streamlit chat interface
├── simple_agent.py     # Emma's AI logic and memory system
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (API keys)
└── README.md          # This file
```

**Simple Two-File Architecture:**

- `app.py`: Streamlit web interface with chat, streaming, and proactive messaging
- `simple_agent.py`: Emma's brain - empathy, memory, LLM integration, and proactive logic

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI-compatible API (Mistral AI recommended)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/MAffan1/personal-assistant-agent.git
cd personal-assistant
```

2. **Create virtual environment**

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file with your API credentials:

```env
MISTRAL_BASE_URL=https://api.mistral.ai/v1
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-tiny-latest
```

5. **Run the application**

```bash
streamlit run app.py
```

6. **Open in browser**
   Navigate to `http://localhost:8501`

## 💬 How Emma Works

### Empathetic AI Assistant

Emma is designed to be more than just a chatbot - she's a caring companion who:

- **Remembers Your Life**: Stores important details about events, people, and emotions you share
- **Shows Genuine Care**: Uses warm, emotional language and asks follow-up questions
- **Proactive Check-ins**: Automatically reaches out when you haven't talked in a while
- **Emotional Support**: Recognizes when you're stressed, excited, or going through something important
- **Smart Follow-ups**: Remembers your meetings, interviews, and important events to ask about later

### Memory System

Emma automatically detects and remembers:

- **Events**: meetings, appointments, interviews, exams, deadlines
- **People**: friends, family members, relationships
- **Emotions**: when you're stressed, worried, excited, or anxious
- **Important Activities**: work, school, vacations, birthdays
- **Health & Wellbeing**: doctor visits, exercise, sleep patterns

### Proactive Engagement

- **Smart Timing**: Follows up on important things after appropriate delays
- **Contextual Check-ins**: Asks about specific things you mentioned before
- **Emotional Awareness**: Reaches out if you seemed troubled in previous conversations
- **Celebration**: Remembers to ask about positive events and achievements

## 💡 Usage Examples

### Natural Conversations with Memory

```
User: "I have a job interview tomorrow morning. I'm pretty nervous about it!"

Emma: "Oh wow, a job interview! I can understand why you'd feel nervous - that's completely normal 😊
       What kind of position is it for? I'm excited for you and I believe you'll do great!
       I'll make sure to check in with you tomorrow to hear how it went ✨"

[Next day, Emma proactively messages:]

Emma: "Hey! I've been thinking about your interview. How did it go? I'm excited to hear! ✨"
```

### Emotional Support & Follow-up

```
User: "Work has been really stressing me out lately. My boss keeps piling on more projects."

Emma: "I can hear that you're feeling really overwhelmed with everything at work 💙
       That sounds incredibly frustrating when your boss keeps adding to your plate.
       How are you taking care of yourself through all this stress?"

[Later proactive check-in:]

Emma: "I've been thinking about you since you mentioned feeling stressed about work.
       How are things going today? I'm here if you need to talk 🤗"
```

### Memory & Relationship Tracking

```
User: "Had dinner with my sister Sarah last night. She's going through a rough breakup."

Emma: "It sounds like Sarah is lucky to have such a caring sibling like you during this difficult time 💕
       Breakups are never easy. How is she holding up? And how are you feeling about supporting her?"

[Future conversation:]

Emma: "How's your sister Sarah doing with everything she's been going through?
       I remember you mentioned she was having a tough time with her breakup."
```

## 🎮 How to Use

### Getting Started

1. **Launch the app** and start chatting with Emma
2. **Share details** about your life - events, people, feelings, plans
3. **Watch Emma remember** important details in the sidebar
4. **Experience proactive check-ins** when Emma reaches out automatically
5. **Observe the empathy** in Emma's responses and follow-up questions

### Tips for Best Experience

- **Be personal**: Share details about your day, relationships, and feelings
- **Mention upcoming events**: Tell Emma about interviews, meetings, or important dates
- **Express emotions**: Let Emma know when you're excited, worried, or stressed
- **Wait for proactive messages**: After 20 seconds of inactivity, Emma may check in
- **Check the sidebar**: View Emma's memories and live interaction status

## 🔮 Future Roadmap

### Current Features ✅

- Empathetic AI personality with emotional intelligence
- Memory system for important events and people
- Proactive messaging and follow-ups
- Streaming chat responses
- Real-time interaction tracking
- Contextual conversation history

### Planned Improvements 🚀

- **Persistent Storage**: Save conversations and memories between sessions
- **Enhanced Memory**: More sophisticated relationship and pattern detection
- **WhatsApp Integration**: Connect to WhatsApp Business API
- **Voice Support**: Process voice messages and respond with audio
- **Multi-User**: Support multiple users with separate memory systems
- **Calendar Integration**: Sync with calendar for better event tracking

## 🔧 Technical Implementation

### Core Components

**`app.py` - Streamlit Interface**

- Chat interface with user and agent message display
- Real-time streaming response generation
- Proactive message checking with auto-refresh fragments
- Memory display sidebar with important memories
- Live interaction status tracking

**`simple_agent.py` - Emma's Brain**

- Empathetic system prompt for emotional intelligence
- Memory extraction from conversations using keyword detection
- Proactive message timing and generation logic
- LLM integration with streaming support (Mistral AI)
- Follow-up system for important events and emotions

### Key Features Implementation

- **Memory System**: Keyword-based extraction stores important events, people, and emotions
- **Proactive Timing**: Checks for follow-ups after 10-15 seconds, general check-ins after 20 seconds
- **Streaming Responses**: Real-time message generation with live typing indicators
- **Empathetic Responses**: Warm, caring language with emotional acknowledgment
- **Fragment Updates**: Streamlit fragments for auto-updating status and proactive message delivery

### Environment Setup

Requires `.env` file with:

```env
MISTRAL_BASE_URL=https://api.mistral.ai/v1
MISTRAL_API_KEY=your_api_key
MISTRAL_MODEL=mistral-tiny-latest
```

## 🤝 Contributing

This is a minimal but functional empathetic AI assistant. Areas for enhancement:

- **Persistent Storage**: Add database for long-term memory
- **Advanced NLP**: Better emotion and context detection
- **Memory Management**: More sophisticated relationship mapping
- **Performance**: Optimize fragment update frequencies
- **UI/UX**: Enhanced chat interface and mobile responsiveness

## 📄 License

MIT License - Feel free to use, modify, and distribute

---

**Built with 💙 by [MAffan1](https://github.com/MAffan1)**

_Emma is designed to be a caring, empathetic companion that genuinely remembers and cares about your wellbeing._
