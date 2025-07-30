# Cal.com AI Scheduling Agent

An intelligent chatbot that uses OpenAI's function calling capabilities to interact with your Cal.com account through natural language. Book, view, cancel, and reschedule meetings through a conversational interface.

![Agent Demo](https://img.shields.io/badge/demo-live-green)


## Quick Start

### Prerequisites
- Docker & Docker Compose
- Cal.com account with API access
- OpenAI API key

### Environment setup

Create a `.env` file in the project root:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Cal.com Configuration
CAL_API_KEY=your_cal_api_key_here
CAL_BASE_URL=https://api.cal.com/v2
CAL_EVENT_TYPE_ID=default_event_type_id
```

### Run the Application
```bash
# Clone and navigate to the project
git clone <repository-url>
cd cal_agent

# Start the full stack
docker-compose up --build

# Visit the application
open http://localhost
```


That's it! The application will be available at `http://localhost` with both the chat UI and API running.

## Features

### Core Scheduling Capabilities
- **📅 Book Meetings**: "Schedule a meeting for tomorrow at 2pm"
- **📋 View Bookings**: "Show me my scheduled events"
- **❌ Cancel Events**: "Cancel my meeting at 3pm today"
- **🔄 Reschedule**: "Move my 2pm meeting to 4pm"
- **🗑️ Bulk Cancel**: "Cancel all my meetings"

### Smart Conversational AI
- **Natural Language Processing**: Understands informal scheduling requests
- **Context Awareness**: Maintains conversation context across interactions
- **Time Intelligence**: Handles relative dates ("tomorrow", "next week")
- **UTC Conversion**: Automatically converts times to proper timezone format
- **Session Persistence**: Remembers conversation history per session

### User Experience
- **Modern Chat Interface**: Clean, responsive Svelte-based UI
- **Real-time Interaction**: Instant responses with loading states
- **Markdown Support**: Rich text formatting in agent responses
- **Error Handling**: Graceful error recovery and user feedback
- **Mobile Friendly**: Works seamlessly across devices

## 🏗️ Project Structure

```
livexai/
├── 📁 rest_server/           # FastAPI Backend
│   ├── main.py              # Application entry point
│   ├── import_routes.py     # Route configuration
│   └── api/
│       └── chat/            # Chat API endpoints
│           ├── models.py    # Request/response models
│           └── post_message.py
│
├── 📁 lib/core/             # Core Agent Logic
│   ├── chat_agent.py       # Main conversation agent
│   ├── cal_client.py       # Cal.com API integration
│   ├── openai_client.py    # OpenAI API wrapper
│   ├── langchain_tools.py   # Dynamic tool generation
│   └── logger.py           # Structured logging
│
├── 📁 chat-ui/             # Svelte Frontend
│   ├── src/
│   │   ├── routes/+page.svelte  # Main chat interface
│   │   ├── lib/components/      # Reusable UI components
│   │   └── app.css             # Global styles
│   ├── static/             # Static assets
│   └── build/              # Production build output
│
├── 📁 deployment/          # Docker Configuration
│   ├── nginx/
│   │   ├── Dockerfile      # Nginx + Static UI container
│   │   └── nginx.conf      # Reverse proxy config
│   └── rest_server/
│       └── Dockerfile      # Python API container
│
├── docker-compose.yml      # Multi-container orchestration
├── pyproject.toml          # Python dependencies
└── README.md
```

## Agent Implementation Details

### Function Calling Architecture
- **Dynamic Tool Generation**: Automatically creates LangChain tools from Python functions
- **Schema Inference**: Uses docstring parsing to generate proper function schemas
- **Type Safety**: Full type annotations throughout the codebase
- **Error Boundaries**: Comprehensive error handling with user-friendly messages

### Supported Cal.com Operations
- `create_booking()` - Schedule new meetings with attendee details
- `get_bookings()` - Retrieve meetings with filtering by email/date/status
- `cancel_booking()` - Cancel specific meetings by UID
- `reschedule_booking()` - Move meetings to new time slots
- `cancel_all_bookings()` - Bulk cancellation with safety confirmations

### Session Management (implemented on API - not in UI)
- UUID-based session tracking
- Conversation history persistence
- Context-aware responses
- Cross-request state management

## 🔧 Areas for Improvement

### Agent Performance Optimizations
- **Model Selection**: Switch from GPT-4-turbo to a reasoning model for reliability and accuracy
- **Tool Definition Optimization**: Move available tools to system message instead of sending with every user message to reduce token usage and improve response times
- **Enhanced Date Parsing**: Implement additional tool calls to parse natural language date/time queries ("next Tuesday at 2pm", "in 3 hours") before scheduling attempts
- **Prompt Engineering**: Fine-tune system prompts and few-shot examples to improve agent understanding and reduce hallucinations

### Extended Cal.com Integration
- **Availability Checking**: Integrate Cal.com slots API to proactively check time availability before booking attempts
- **Multiple Meeting Types**: Support different Cal.com event types (15min, 30min, 1hr meetings) and let users specify preferences
- **Advanced Booking Features**: Implement meeting descriptions, location preferences, and guest invitation capabilities
- **Calendar Conflict Detection**: Check for existing meetings and suggest alternative times when conflicts are detected

### Testing & Quality Assurance
- **Unit Testing**: Comprehensive test suite for all Python methods in `lib/core/` modules
- **Integration Testing**: Test Cal.com API interactions with mock responses and error scenarios
- **Agent Testing**: Validate conversation flows, tool calling accuracy, and edge case handling
- **Prompt Testing**: A/B test different system prompts and measure agent performance metrics
