# ============= PERSONAL ASSISTANT CONFIGURATION =============
"""
Configuration file for Emma - Personal Assistant AI Agent
Modify these values to customize timing and behavior
"""

# ============= PROACTIVE MESSAGING TIMING =============
# All timing values are in minutes

# How long to wait before following up on important topics (meetings, interviews, etc.)
FOLLOW_UP_DELAY_MINUTES = 1

# How long to wait before sending general check-in messages  
GENERAL_CHECKIN_MINUTES = 2

# How long after detecting important info to schedule a follow-up
MEMORY_FOLLOWUP_MINUTES = 1

# ============= AGENT BEHAVIOR SETTINGS =============

# Maximum number of conversation messages to include in LLM context
MAX_CONVERSATION_CONTEXT = 6

# LLM response parameters
LLM_TEMPERATURE = 0.8  # Higher = more creative/varied responses
LLM_MAX_TOKENS = 200

# ============= UI SETTINGS =============

# How often to update the live status display (seconds)
STATUS_UPDATE_FREQUENCY = 5

# How often to check for proactive messages (seconds)  
PROACTIVE_CHECK_FREQUENCY = 3

# Maximum number of memories to show in sidebar
MAX_MEMORIES_DISPLAYED = 3

# ============= MEMORY SYSTEM =============

# Keywords that trigger memory creation and follow-ups
IMPORTANT_KEYWORDS = [
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

# ============= LOGGING CONFIGURATION =============

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# Log file name
LOG_FILE = "app.log"