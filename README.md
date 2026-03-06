# 🤖 LLM-Driven Multi-Agent Android QA System mark2

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)
[![Android](https://img.shields.io/badge/Android-ADB-orange.svg)](https://developer.android.com/studio/command-line/adb)

> **Advanced Multi-Agent System for Automated Android UI Testing and Quality Assurance**

A sophisticated framework that leverages Large Language Models (LLMs) to orchestrate multiple AI agents for automated Android application testing, UI interaction, and quality assurance. This system implements a hierarchical planning architecture with specialized agents for planning, execution, verification, and supervision.

**🎯 Focused & Streamlined**: This project has been cleaned up to focus on two core functionalities:
1. **Multi-Agent Android Automation** - Execute natural language goals on Android devices
2. **Image-Based Task Analysis** - Analyze screenshots and execute identified tasks

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [🚀 Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [📦 Installation & Setup](#-installation--setup)
- [🔧 Configuration](#-configuration)
- [💻 Usage Examples](#-usage-examples)
- [🔍 API Reference](#-api-reference)
- [🧪 Testing & Evaluation](#-testing--evaluation)
- [🔒 Security](#-security)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

## 🎯 Project Overview

### What is This Project?

The **LLM-Driven Multi-Agent Android QA System mark2** is a cutting-edge automation framework that combines the power of Large Language Models with multi-agent orchestration to perform intelligent Android application testing. Unlike traditional UI automation tools, this system uses AI agents that can:

- **Understand natural language goals** and translate them into actionable UI sequences
- **Adapt to dynamic UI changes** through real-time analysis and planning
- **Learn from previous interactions** to improve future performance
- **Self-verify actions** to ensure successful task completion
- **Handle complex, multi-step workflows** with contextual awareness

### Core Philosophy

This project embodies several key principles:

- **🤖 AI-First Approach**: LLMs drive decision-making, not hardcoded rules
- **🔗 Multi-Agent Collaboration**: Specialized agents work together for complex tasks
- **🧠 Hierarchical Planning**: Break down complex goals into manageable steps
- **📚 Memory & Learning**: Agents remember and learn from past interactions
- **🔄 Self-Verification**: Continuous validation of actions and outcomes
- **🛡️ Safety & Reliability**: Robust error handling and fallback mechanisms

### Use Cases

- **🧪 Automated Testing**: Comprehensive UI testing without manual test scripts
- **🔍 Quality Assurance**: Automated validation of app functionality and user flows
- **📱 Accessibility Testing**: Ensuring apps work for users with disabilities
- **🚀 CI/CD Integration**: Automated testing in continuous integration pipelines
- **📊 Performance Monitoring**: Automated performance testing and monitoring
- **🎯 User Experience Validation**: Automated UX testing and validation

## 🚀 Key Features

### 🧠 Intelligent Planning
- **Natural Language Goal Processing**: Convert human-readable goals into executable plans
- **Hierarchical Task Decomposition**: Break complex tasks into manageable sub-tasks
- **Context-Aware Decision Making**: Consider current UI state and history for optimal actions
- **Adaptive Planning**: Modify plans based on execution results and UI changes

### 🤖 Multi-Agent Architecture
- **Planner Agent**: Converts goals into actionable steps using LLM reasoning
- **Executor Agent**: Performs UI interactions with high precision and reliability
- **Verifier Agent**: Validates action outcomes and ensures task completion
- **Supervisor Agent**: Orchestrates agents and maintains system-wide metrics

### 📱 Advanced Android Integration
- **ADB Integration**: Direct Android Debug Bridge communication for reliable device control
- **UI Tree Analysis**: Real-time parsing and analysis of Android UI hierarchies
- **Gesture Recognition**: Precise tap, scroll, and key press operations
- **Screenshot Capture**: Automatic visual documentation of test execution

### 🧠 Memory & Learning Systems
- **Episodic Memory**: Short-term memory for current task context
- **Narrative Memory**: Long-term storage for cross-episode learning
- **Similarity-Based Retrieval**: Find relevant past experiences for current tasks
- **Performance Analytics**: Track and analyze agent performance over time

### 🔒 Security & Reliability
- **Environment Variable Management**: Secure handling of API keys and sensitive data
- **Error Recovery**: Robust error handling and automatic retry mechanisms
- **Validation Systems**: Multi-layer verification of actions and outcomes
- **Safe Execution**: Controlled execution environment with proper isolation

### 📊 Comprehensive Evaluation
- **Success Rate Tracking**: Measure task completion success rates
- **Performance Metrics**: Track execution time and efficiency
- **Detailed Logging**: Comprehensive logging for debugging and analysis
- **Visual Documentation**: Automatic screenshot capture for audit trails

## 🏗️ Architecture

### System Overview

<img width="1728" height="903" alt="image" src="https://github.com/user-attachments/assets/6202d252-b5ec-4f14-9ece-84367800d6fa" />

### Core Components

The system consists of four specialized AI agents working together:

1. **🤔 Planner Agent** - Converts user goals into executable action sequences
2. **⚡ Executor Agent** - Performs UI actions on Android devices  
3. **✅ Verifier Agent** - Validates action outcomes and ensures task completion
4. **🎯 Supervisor Agent** - Orchestrates agents and maintains system metrics

### Agent Responsibilities

#### 🤔 **Planner Agent** (`agents/llm_planner_agent.py`)
- **Primary Function**: Converts user goals into executable action sequences
- **Key Capabilities**:
  - Natural language goal interpretation
  - Hierarchical task decomposition
  - Context-aware action planning
  - Dynamic plan adaptation
- **Input**: User goal, current UI state, execution history
- **Output**: Structured action plans with rationale

#### ⚡ **Executor Agent** (`agents/llm_executor_agent.py`)
- **Primary Function**: Executes planned actions on Android devices
- **Key Capabilities**:
  - Precise UI element targeting
  - Gesture execution (tap, scroll, key press)
  - App launching and navigation
  - Error handling and recovery
- **Input**: Action plans from Planner Agent
- **Output**: Execution reports with success/failure status

#### ✅ **Verifier Agent** (`agents/llm_verifier_agent.py`)
- **Primary Function**: Validates action outcomes and ensures task completion
- **Key Capabilities**:
  - UI state verification
  - Goal completion validation
  - Success/failure determination
  - Quality assurance checks
- **Input**: Execution reports and current UI state
- **Output**: Verification results and confidence scores

#### 🎯 **Supervisor Agent** (`agents/llm_supervisor_agent.py`)
- **Primary Function**: Orchestrates agents and maintains system metrics
- **Key Capabilities**:
  - Agent coordination and synchronization
  - Performance monitoring and analytics
  - Episode management and completion
  - Long-term learning and optimization
- **Input**: Reports from all agents
- **Output**: System metrics and episode summaries

### Core Components

#### 📡 **Message Bus** (`core/message_bus.py`)
- **Purpose**: Lightweight in-process pub/sub communication system
- **Features**:
  - Asynchronous message passing between agents
  - Type-safe message structure
  - Automatic message routing
  - Event-driven architecture

#### 🧠 **Memory System** (`core/memory.py`)
- **Episodic Memory**: Short-term storage for current task context
- **Narrative Memory**: Long-term storage for cross-episode learning
- **Features**:
  - Tag-based retrieval
  - Similarity-based search
  - Persistent storage
  - JSON export capabilities

#### 🔧 **Configuration Management** (`core/config.py`)
- **Purpose**: Centralized configuration and environment management
- **Features**:
  - Environment variable loading
  - Secure API key management
  - Configurable settings
  - Validation and error handling

#### 🤖 **LLM Client** (`core/llm_client.py`)
- **Purpose**: OpenAI API integration with structured output
- **Features**:
  - Structured action generation
  - Context-aware prompting
  - Error handling and retry logic
  - Configurable model selection

### Data Flow

1. **Goal Input**: User provides natural language goal
2. **Planning Phase**: Planner Agent converts goal to action plan
3. **Execution Phase**: Executor Agent performs UI actions
4. **Verification Phase**: Verifier Agent validates outcomes
5. **Supervision Phase**: Supervisor Agent coordinates and tracks progress
6. **Memory Update**: Results stored in memory for future learning
7. **Iteration**: Process continues until goal completion or failure

## 📦 Installation & Setup

### Prerequisites

- **Python 3.7+** (Required for type annotations and modern features)
- **Android SDK** with ADB tools
- **Android Emulator** or physical device
- **OpenAI API Key** (Required for LLM functionality)

### Step-by-Step Installation

#### 1. **Clone the Repository**
```bash
git clone https://github.com/baliutkarsh2/multi_agent_qa.git
cd multi_agent_qa
```

#### 2. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

#### 3. **Set Up Environment Variables**
```bash
# Run the automated setup script
python setup.py

# Edit the .env file with your API key
# OPENAI_API_KEY=your_actual_api_key_here
```

#### 4. **Initialize Project Directories**
```bash
python init_dirs.py
```

#### 5. **Verify Configuration**
```bash
python check_env.py
```

#### 6. **Set Up Android Environment**
```bash
# To begin, add the Android SDK emulator directory to your system's environment variables.

Path:
C:\Users\<User>\AppData\Local\Android\Sdk\emulator

# Run cmd as Administrator and Start Android emulator
emulator -avd Pixel_8 -port 5554

# Or connect physical device via USB debugging
adb devices
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes | - |
| `ANDROID_EMULATOR_SERIAL` | Android device serial | - | `emulator-5554` |
| `LOG_LEVEL` | Logging verbosity | - | `INFO` |
| `MEMORY_STORE_PATH` | Memory storage directory | - | `memory_store` |
| `SCREENSHOT_DIR` | Screenshot storage directory | - | `logs/screenshots` |

### Project Structure

```
multi_agent_qa/
├── 📁 agents/                    # AI Agent Implementations
│   ├── llm_planner_agent.py     # Goal planning and task decomposition
│   ├── llm_executor_agent.py    # UI action execution
│   ├── llm_verifier_agent.py    # Action verification and validation
│   └── llm_supervisor_agent.py  # Agent orchestration and metrics
├── 📁 core/                     # Core System Components
│   ├── action_schema.py         # Action type definitions
│   ├── config.py               # Configuration management
│   ├── env_loader.py           # Environment variable loading
│   ├── episode.py              # Episode context management
│   ├── llm_client.py           # OpenAI API integration
│   ├── logging_config.py       # Logging configuration
│   ├── memory.py               # Memory system implementation
│   ├── message_bus.py          # Inter-agent communication
│   ├── registry.py             # Agent registration system
│   ├── run_logger.py           # Run logging system
│   └── run_logger_integration.py # Run logger integration
├── 📁 env/                      # Environment Interfaces
│   ├── android_interface.py    # Android device abstraction
│   ├── gesture_utils.py        # Gesture execution utilities
│   └── ui_utils.py             # UI element parsing and selection
├── 📁 evaluation/               # Evaluation and Metrics
│   ├── evaluator.py            # Episode evaluation logic
│   └── metrics.py              # Performance metrics calculation
├── 📁 runners/                  # Application Runners
│   └── run_example.py          # Main execution runner
├── 📁 test_aitw_videos/        # Test images for image pipeline
│   ├── demo1.png               # Sample test image
│   └── ...                     # Additional test images
├── 📁 logs/                     # Logs and Screenshots (auto-created)
├── 📁 memory_store/            # Memory Storage (auto-created)
├── 📄 .env                      # Environment variables (user-created)
├── 📄 .gitignore               # Git ignore rules
├── 📄 README.md                # This file
├── 📄 requirements.txt         # Python dependencies
├── 📄 setup.py                 # Automated setup script
├── 📄 init_dirs.py             # Directory initialization
├── 📄 check_env.py             # Environment verification
├── 📄 env_example.txt          # Environment template
└── 📄 run_individual_image_pipeline.py # Image analysis pipeline
```

## 🔧 Configuration

### Configuration Files

The system uses environment variables for configuration. No additional configuration files are required.

#### **Environment Configuration** (`.env`)
```bash
# API Keys and Sensitive Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANDROID_EMULATOR_SERIAL=emulator-5554
LOG_LEVEL=INFO
MEMORY_STORE_PATH=memory_store
SCREENSHOT_DIR=logs/screenshots
```

### Action Schemas

The system supports the following action types:

#### **Launch App Action**
```json
{
  "step_id": "unique_id",
  "action": "launch_app",
  "package": "com.example.app",
  "rationale": "Need to open the target application"
}
```

#### **Tap Action**
```json
{
  "step_id": "unique_id",
  "action": "tap",
  "resource_id": "com.example:id/button",
  "text": "Submit",
  "order": 1,
  "rationale": "Tap the submit button to proceed"
}
```

#### **Press Key Action**
```json
{
  "step_id": "unique_id",
  "action": "press_key",
  "key": "enter",
  "rationale": "Submit the form"
}
```

#### **Scroll Action**
```json
{
  "step_id": "unique_id",
  "action": "scroll",
  "direction": "down",
  "until_resource_id": "com.example:id/target",
  "rationale": "Scroll to find the target element"
}
```

#### **Verify Action**
```json
{
  "step_id": "unique_id",
  "action": "verify",
  "resource_id": "com.example:id/success",
  "rationale": "Verify the action was successful"
}
```

#### **Wait Action**
```json
{
  "step_id": "unique_id",
  "action": "wait",
  "duration": 2.0,
  "rationale": "Wait for the page to load"
}
```

## 💻 Usage Examples

### **Primary Commands**

The system supports two main execution modes:

#### **1. Multi-Agent Android Automation**
Execute natural language goals on Android devices using the multi-agent system:

```bash
python -m runners.run_example --goal "Enable Wi-Fi in Android settings" --serial emulator-5554
```

**What this does:**
- Analyzes your natural language goal
- Plans the required UI actions
- Executes the actions on the Android device
- Verifies each step was successful
- Provides detailed execution logs

#### **2. Image-Based Task Analysis**
Analyze Android screenshots and execute the identified tasks:

```bash
python run_individual_image_pipeline.py --image demo1.png
```

**What this does:**
- Uses OpenAI Vision API to analyze the screenshot
- Extracts the task the user was trying to complete
- Executes the task using the multi-agent system
- Provides performance evaluation and metrics

### **Example Goals for Multi-Agent System**

```bash
# Settings and Configuration
--goal "Enable Wi-Fi in Android settings"
--goal "Turn on Bluetooth in device settings"
--goal "Change screen brightness to maximum"

# App Navigation
--goal "Open Chrome and scroll through articles"
--goal "Launch Gmail and open my inbox"
--goal "Open Camera app and take a photo"

# System Operations
--goal "Go to home screen and open app drawer"
--goal "Check battery percentage in quick settings"
--goal "Enable airplane mode"
```

### **Advanced Usage**

#### **Custom Device Configuration**
```bash
# Use specific device serial
python -m runners.run_example --goal "Your goal here" --serial device_serial_number

# Use default device (emulator-5554)
python -m runners.run_example --goal "Your goal here"
```

#### **Image Pipeline Options**
```bash
# Process all available test images
python run_individual_image_pipeline.py --all

# List available test images
python run_individual_image_pipeline.py --list

# Process specific image with custom options
python run_individual_image_pipeline.py --image demo1.png --no-save
```

## 🔍 API Reference

### Core Classes

#### **LLMClient** (`core/llm_client.py`)
```python
class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini")
    def request_next_action(self, goal: str, ui_xml: str, history: list[Dict[str,Any]]) -> Dict[str,Any]
    def verify_action(self, action_description: str, ui_xml: str) -> Dict[str, Any]
```

#### **AndroidDevice** (`env/android_interface.py`)
```python
class AndroidDevice:
    def __init__(self, serial: Optional[str]=None)
    def get_ui_tree(self) -> UIState
    def launch_app(self, pkg: str) -> None
    def press_key(self, key: str) -> None
    def type_text(self, text: str) -> None
    def screenshot(self, label: str) -> str
    def scroll(self, direction: str) -> None
```

#### **EpisodicMemory** (`core/memory.py`)
```python
class EpisodicMemory:
    def store(self, key: str, value: Any, tags: List[str] | None = None) -> None
    def retrieve(self, key: str) -> Any | None
    def retrieve_similar(self, query: str, k: int = 3) -> List[Any]
```

#### **RunLogger** (`core/run_logger.py`)
```python
class RunLogger:
    def __init__(self, run_id: str, user_goal: str, logs_dir: str = "logs")
    def log_event(self, event_type: str, agent: str, data: Dict[str, Any]) -> None
    def log_step_execution(self, episode_id: str, step: Dict, result: Dict, ui_snapshot: str) -> None
```

### Agent Registration

#### **Registering Custom Agents**
```python
from core.registry import register_agent

@register_agent("custom_agent")
class CustomAgent:
    def __init__(self):
        # Agent initialization
        pass
    
    def act(self, *args, **kwargs):
        # Agent action logic
        pass
```

#### **Using Registered Agents**
```python
from core.registry import get_agent

agent_class = get_agent("custom_agent")
agent_instance = agent_class()
```

### Message Bus

#### **Publishing Messages**
```python
from core.message_bus import publish, Message

message = Message(
    sender="my_agent",
    channel="custom_channel",
    payload={"data": "value"}
)
publish(message)
```

#### **Subscribing to Messages**
```python
from core.message_bus import subscribe

def message_handler(msg: Message):
    print(f"Received: {msg.payload}")

subscribe("custom_channel", message_handler)
```

## 🧪 Evaluation

### Evaluation Metrics

#### **Success Rate**
- **Definition**: Percentage of successfully completed tasks
- **Calculation**: `successful_episodes / total_episodes`
- **Target**: >90% for production use

#### **Average Duration**
- **Definition**: Mean time to complete tasks
- **Calculation**: `sum(durations) / count(episodes)`
- **Optimization**: Minimize while maintaining success rate

#### **Verification Accuracy**
- **Definition**: Accuracy of action verification
- **Calculation**: `correct_verifications / total_verifications`
- **Target**: >95% verification accuracy

### **Image Pipeline Evaluation**

The image analysis pipeline provides additional evaluation metrics:

#### **Task Extraction Accuracy**
- **Definition**: How well the system identifies tasks from screenshots
- **Method**: OpenAI Vision API analysis with human validation

#### **Execution Performance**
- **Definition**: How well the multi-agent system executes identified tasks
- **Metrics**: Step-by-step accuracy, robustness, and generalization scores

#### **Performance Grading**
- **🟢 EXCELLENT (≥0.8)**: System performing exceptionally well
- **🟡 GOOD (0.6-0.8)**: System performing well with consistent results
- **🟠 FAIR (0.4-0.6)**: System shows mixed performance
- **🔴 POOR (<0.4)**: System requires significant improvements

### Debugging and Logging

#### **Log Levels**
- **DEBUG**: Detailed execution information
- **INFO**: General execution flow
- **WARNING**: Potential issues
- **ERROR**: Execution failures

#### **Log Output**
```bash
2025-07-25 20:12:05,385 | LLM-PLANNER     | INFO     | Planning next action for goal: Enable Wi-Fi
2025-07-25 20:12:06,235 | LLM-EXECUTOR    | INFO     | Executing step: {'action': 'tap', 'resource_id': 'com.android.settings:id/wifi_settings'}
2025-07-25 20:12:07,123 | LLM-VERIFIER    | INFO     | Verifying step: {'action': 'verify', 'text': 'Wi-Fi'}
```

## 🔒 Security

### API Key Management

- **Environment Variables**: All sensitive data stored in `.env` file
- **Git Exclusion**: `.env` file automatically excluded from version control
- **Validation**: Runtime validation of required environment variables
- **Error Handling**: Graceful handling of missing or invalid credentials

### Safe Execution

- **Controlled Environment**: All actions executed in controlled Android environment
- **Validation**: Multi-layer validation of actions before execution
- **Error Recovery**: Automatic error detection and recovery mechanisms
- **Audit Trail**: Comprehensive logging of all actions and outcomes

### Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong API keys** with appropriate permissions
3. **Regular key rotation** for production environments
4. **Monitor API usage** to detect unusual activity
5. **Limit device access** to authorized devices only

## 🤝 Contributing

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/multi_agent_qa.git
cd multi_agent_qa

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

```

### Coding Standards

- **Python Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type annotations for all functions
- **Documentation**: Include docstrings for all public methods
- **Testing**: Maintain >80% code coverage
- **Logging**: Use structured logging with appropriate levels

### Pull Request Guidelines

1. **Clear Description**: Explain what the PR does and why
2. **Tests**: Include tests for new functionality
3. **Documentation**: Update README and docstrings as needed
4. **Code Review**: Address all review comments
5. **CI/CD**: Ensure all checks pass

### Issue Reporting

When reporting issues, please include:

- **Environment**: OS, Python version, Android SDK version
- **Steps to Reproduce**: Clear, step-by-step instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Logs**: Relevant log output
- **Screenshots**: If applicable

## 🙏 Acknowledgments

### Research Foundations

This project builds upon significant research in:

- **Multi-Agent Systems**: Collaborative AI agent architectures
- **Hierarchical Planning**: Complex task decomposition strategies
- **LLM Integration**: Large language model applications in automation
- **Android Automation**: Mobile device testing and interaction
---

## 📞 Support & Contact

- **Email**: [baliutkarsh2@gmail.com](mailto:baliutkarsh2@gmail.com)

---

*This project represents the cutting edge of AI-driven automation, combining the power of large language models with sophisticated multi-agent orchestration to create a truly intelligent Android testing system.*