from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

class AgentState(TypedDict):
    target: str
    findings: str
    poc_status: str
    messages: List[str]

def create_graph(researcher_agent, poc_agent):
    """Creates the LangGraph workflow with injected agent graphs."""

    def researcher_node(state: AgentState):
        target = state["target"]
        print(f"--- Researcher Working on {target} ---")
        
        # Invoke the researcher graph
        # It expects a list of messages or a string which converts to a HumanMessage
        result = researcher_agent.invoke({"messages": [HumanMessage(content=f"Analyze this target: {target}")]})
        
        # Result is the final state of the agent graph
        messages = result["messages"]
        last_message = messages[-1]
        findings = last_message.content
        
        return {"findings": findings}

    def poc_node(state: AgentState):
        findings = state["findings"]
        print(f"--- PoC Creator Working on findings ---")
        
        # Invoke the PoC graph
        result = poc_agent.invoke({"messages": [HumanMessage(content=f"Create a PoC for these findings: {findings}")]})
        
        messages = result["messages"]
        last_message = messages[-1]
        poc_status = last_message.content
        
        return {"poc_status": poc_status}

    def should_create_poc(state: AgentState):
        findings = state["findings"].lower()
        if "no vulnerability" in findings or "no bugs" in findings:
            return "end"
        return "create_poc"

    workflow = StateGraph(AgentState)

    workflow.add_node("researcher", researcher_node)
    workflow.add_node("poc_creator", poc_node)

    workflow.set_entry_point("researcher")

    workflow.add_conditional_edges(
        "researcher",
        should_create_poc,
        {
            "create_poc": "poc_creator",
            "end": END
        }
    )

    workflow.add_edge("poc_creator", END)

    return workflow.compile()
