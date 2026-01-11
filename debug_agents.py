import os
from agents import create_agents
from dotenv import load_dotenv

load_dotenv()

# Mock Config
config = {
    "researcher": {
        "provider": "Ollama",
        "model": "llama3",
        "base_url": "http://localhost:11434/v1",
        "api_key": None
    },
    "poc": {
        "provider": "Ollama",
        "model": "llama3",
        "base_url": "http://localhost:11434/v1",
        "api_key": None
    }
}

print("--- Testing create_agents ---")
try:
    # Import internals to debug
    from agents import get_llm, researcher_prompt_template
    from tools import (
        list_folders, list_files, view_file, create_file, 
        search_files, regex_search, run_security_audit, terminal_command
    )
    researcher_tools = [
        list_folders, list_files, view_file, 
        search_files, regex_search, run_security_audit, 
        terminal_command
    ]
    from langchain_core.prompts import PromptTemplate
    from langchain.agents import create_react_agent
    
    print(f"Tools count: {len(researcher_tools)}")
    for i, t in enumerate(researcher_tools):
        print(f"Tool {i}: {type(t)} - {t.name if hasattr(t, 'name') else 'No Name'}")
        if t is None:
            print(f"ERROR: Tool {i} is None!")

    llm = get_llm("Ollama", "llama3")
    print(f"LLM: {type(llm)}")
    
    prompt = PromptTemplate.from_template(researcher_prompt_template)
    print(f"Prompt: {type(prompt)}")
    
    from langchain_core.runnables import RunnablePassthrough
    from langchain.agents.format_scratchpad import format_log_to_str
    
    print(f"format_log_to_str: {type(format_log_to_str)}")
    
    print("--- Testing RunnablePassthrough.assign ---")
    try:
        assign = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_log_to_str(x["intermediate_steps"])
        )
        print(f"Assign created: {type(assign)}")
    except Exception as e:
        print(f"Assign FAILED: {e}")
        import traceback
        traceback.print_exc()

    agent = create_react_agent(llm, researcher_tools, prompt)
    print(f"Agent: {type(agent)}")
    
    if agent is None:
        print("CRITICAL: create_react_agent returned None!")

    researcher_executor, poc_executor = create_agents(config)
    print(f"Researcher Executor: {type(researcher_executor)}")
    print(f"PoC Executor: {type(poc_executor)}")

    if researcher_executor is None:
        print("ERROR: Researcher Executor is None")
    if poc_executor is None:
        print("ERROR: PoC Executor is None")

    # Test Graph
    print("--- Testing Graph Creation ---")
    from graph import create_graph
    app = create_graph(researcher_executor, poc_executor)
    print(f"Graph App: {type(app)}")
    
    print("--- Testing Graph Invoke ---")
    initial_state = {
        "target": "test",
        "findings": "",
        "poc_status": "",
        "messages": []
    }
    app.invoke(initial_state)

except Exception as e:
    print(f"EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
