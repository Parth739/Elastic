# Simple LangGraph Chatbot

## Overview
It demonstrates the fundamentals of creating a stateful AI agent with graph-based architecture.

## What This Bot Does

- **Accepts user input** in a continuous loop
- **Sends messages to Gemini AI** for processing
- **Displays AI responses** in the terminal
- **Runs until** the user types "exit"

## Setup Instructions

#### **1. Install Dependencies**
```bash
pip install langgraph google-generativeai python-dotenv langchain-core
```

#### **2. Create .env File**
Create a `.env` file in your project directory:
```
GEMENI_API_KEY=your_gemini_api_key_here
```

#### **3. Run the Bot**
```bash
python your_bot_file.py
```

## How It Works

### **State Management**
```python
class AgentState(TypedDict):
    messages: List[HumanMessage]
```
The bot uses a TypedDict to define the state structure that holds conversation messages.

### **Processing Function**
```python
def process(state: AgentState) -> AgentState:
    response = model.generate_content(state['messages'])
    print(f"\n Ai :{response.text}")
    return state
```
This function takes the current state, sends messages to Gemini, and prints the response.

### **Graph Structure**
```python
graph = StateGraph(AgentState)
graph.add_node("processor", process)
graph.add_edge(START, "processor")
graph.add_edge("processor", END)
```
The bot creates a simple linear graph: **START → processor → END**

### **Conversation Loop**
```python
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break
    result = app.invoke({"messages": user_input})
```
Continuously accepts user input and processes it through the graph until "exit" is typed.
