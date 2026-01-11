import streamlit as st
import os
import sys
from dotenv import load_dotenv

load_dotenv()

st.title("Debug Agent Creation")

st.write(f"Python Executable: {sys.executable}")
st.write(f"CWD: {os.getcwd()}")

try:
    st.subheader("Imports")
    from agents import get_llm, researcher_prompt_template
    from tools import (
        list_folders, list_files, view_file, create_file, 
        search_files, regex_search, run_security_audit, terminal_command
    )
    from langchain_core.prompts import PromptTemplate
    from langchain.agents import create_react_agent
    from langchain_core.runnables import RunnablePassthrough
    from langchain.agents.format_scratchpad import format_log_to_str
    
    st.success("Imports successful")
    
    st.write(f"format_log_to_str: {type(format_log_to_str)}")
    
    st.subheader("Tools Setup")
    researcher_tools = [
        list_folders, list_files, view_file, 
        search_files, regex_search, run_security_audit, 
        terminal_command
    ]
    st.write(f"Tools count: {len(researcher_tools)}")
    
    st.subheader("LLM Setup")
    llm = get_llm("Ollama", "llama3")
    st.write(f"LLM: {type(llm)}")
    
    st.subheader("Prompt Setup")
    prompt = PromptTemplate.from_template(researcher_prompt_template)
    st.write(f"Prompt: {type(prompt)}")
    
    st.subheader("RunnablePassthrough Test")
    try:
        assign = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_log_to_str(x["intermediate_steps"])
        )
        st.write(f"Assign created: {type(assign)}")
    except Exception as e:
        st.error(f"Assign FAILED: {e}")
        st.exception(e)

    st.subheader("Agent Creation")
    try:
        agent = create_react_agent(llm, researcher_tools, prompt)
        st.write(f"Agent created: {type(agent)}")
    except Exception as e:
        st.error(f"Agent Creation FAILED: {e}")
        st.exception(e)

except Exception as e:
    st.error(f"Global Error: {e}")
    st.exception(e)
