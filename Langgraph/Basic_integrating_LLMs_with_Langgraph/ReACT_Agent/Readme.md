# LangGraph Agent with Tool Integration
https://medium.com/cyberark-engineering/building-production-ready-ai-agents-with-langgraph-a-real-life-use-case-7bda34c7f4e4
## Overview

How to build an **AI agent with tool-calling capabilities** using LangGraph. The agent can perform mathematical operations and engage in conversation, showcasing key concepts in building stateful, tool-equipped AI systems.

## THings to learn from this 

- **State Management** with `Annotated` types and `add_messages` reducer
- **Tool Integration** using LangChain's `@tool` decorator
- **Conditional Routing** to handle tool calls vs regular responses
- **Message Types** and their roles in agent communication
- **Streaming Responses** for real-time output

## Key Concepts Explained

### **1. Advanced State Management**

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

**What we learned:**
- `Annotated` provides additional metadata without changing the type 
- `add_messages` is a **reducer function** that automatically handles message appending
- This pattern ensures messages are properly accumulated in the conversation history

### **2. Tool Definition**

```python
@tool
def add(a: int, b: int):
    """This is an addition function that adds 2 numbers together"""
    return a + b
```

**What we learned:**
- The `@tool` decorator converts regular Python functions into LangChain tools
- **Docstrings are crucial** - they help the LLM understand when and how to use the tool
- Type hints ensure proper parameter validation

### **3. Model Binding**

```python
model = ChatOpenAI(model="gpt-4o").bind_tools(tools)
```

**What we learned:**
- `bind_tools()` gives the model access to our defined tools
- The model can now decide when to call tools based on user input

### **4. Conditional Routing**

```python
def should_continue(state: AgentState): 
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls: 
        return "end"
    else:
        return "continue"
```

**What we learned:**
- The agent checks if the last message contains tool calls
- Returns different paths based on whether tools need to be executed
- This creates a **dynamic workflow** that adapts to the conversation

### **5. Graph Construction**

```python
graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)
```

**What we learned:**
- **Conditional edges** create branching logic in our graph
- The agent can loop between calling tools and generating responses
- This pattern enables complex multi-step reasoning

## Message Types Explained

#### **BaseMessage**
The parent class for all message types - provides the foundation for the messaging system

#### **SystemMessage**
Used to give instructions to the AI:
```python
SystemMessage(content="You are my AI assistant...")
```

#### **ToolMessage**
Carries results from tool execution back to the model, including:
- Tool output content
- `tool_call_id` for matching responses to requests

## The Agent Workflow

1. **User Input** → Agent receives the message
2. **Model Decision** → GPT-4 analyzes if tools are needed
3. **Tool Calling** → If needed, appropriate tools are invoked
4. **Result Processing** → Tool results are sent back to the model
5. **Final Response** → Model generates a comprehensive answer

## Code Flow Visualization

```
START → our_agent → should_continue?
                           ↓
                    [if tool_calls]
                           ↓
                        tools
                           ↓
                      our_agent
                           ↓
                    [if no tool_calls]
                           ↓
                          END
```

## Running the Example

The provided example demonstrates:
```python
inputs = {"messages": [("user", "Add 40 + 12 and then multiply the result by 6. Also tell me a joke please.")]}
```

**What happens:**
1. Agent recognizes two tasks: math calculation and joke request
2. Calls `add(40, 12)` → returns 52
3. Calls `multiply(52, 6)` → returns 312
4. Generates a joke alongside the calculation result


We can build on this basic example to 
- Add more complex tools
- Create custom reducers for specialized state management
- Build multi-agent systems where agents collaborate using tools

