import streamlit as st
import os
from agents import create_agents
from graph import create_graph
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Bug Bounty Agent", layout="wide")

st.title("🕷️ AI Bug Bounty Agent")
st.markdown("""
This multi-agent system uses **LangGraph** and **Uncensored LLMs** to:
1.  **Research**: Find vulnerabilities in a target (URL, IP, Repo, Directory).
2.  **Exploit**: Create a `ProofOfConcept.py` to demonstrate the finding.
""")

# --- Sidebar Configuration ---
st.sidebar.header("Agent Configuration")

def render_agent_config(agent_name, key_prefix):
    st.sidebar.subheader(f"{agent_name} Settings")
    provider = st.sidebar.selectbox(
        "Provider", 
        ["Ollama", "OpenAI", "OpenRouter", "Gemini"], 
        key=f"{key_prefix}_provider"
    )
    
    model = st.sidebar.text_input(
        "Model Name", 
        value="llama3" if provider == "Ollama" else ("gpt-4o" if provider == "OpenAI" else "gemini-1.5-pro"),
        key=f"{key_prefix}_model"
    )
    
    base_url = None
    api_key = None
    
    if provider == "Ollama":
        base_url = st.sidebar.text_input(
            "Base URL", 
            value="http://localhost:11434/v1", 
            key=f"{key_prefix}_url"
        )
    elif provider == "OpenAI":
        api_key = st.sidebar.text_input(
            "API Key", 
            type="password", 
            value=os.getenv("OPENAI_API_KEY", ""),
            key=f"{key_prefix}_key"
        )
    elif provider == "OpenRouter":
        api_key = st.sidebar.text_input(
            "API Key", 
            type="password", 
            value=os.getenv("OPENROUTER_API_KEY", ""),
            key=f"{key_prefix}_key"
        )
    elif provider == "Gemini":
        api_key = st.sidebar.text_input(
            "API Key", 
            type="password", 
            value=os.getenv("GOOGLE_API_KEY", ""),
            key=f"{key_prefix}_key"
        )
        
    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key
    }

researcher_config = render_agent_config("Security Researcher", "res")
st.sidebar.markdown("---")
poc_config = render_agent_config("PoC Creator", "poc")

# --- Main App ---

target_input = st.text_input("Enter Target (URL, IP, Path to Repo/Directory):", placeholder="/home/reni/Codes/Python/Bug-Bounty_Agent/vulnerable_app.py")

if st.button("Start Scan"):
    if not target_input:
        st.error("Please enter a target.")
    else:
        st.info(f"Starting analysis on: {target_input}")
        
        try:
            with st.spinner("Initializing Agents..."):
                # Create Agents based on config
                config = {
                    "researcher": researcher_config,
                    "poc": poc_config
                }
                researcher_executor, poc_executor = create_agents(config)
                
                # Create Graph
                app = create_graph(researcher_executor, poc_executor)
            
            with st.spinner("Agents are working... Check terminal for detailed logs."):
                initial_state = {
                    "target": target_input,
                    "findings": "",
                    "poc_status": "",
                    "messages": []
                }
                
                final_state = app.invoke(initial_state)
                
                st.success("Analysis Complete!")
                
                # Show detailed logs
                with st.expander("View Detailed Execution Logs"):
                    for msg in final_state.get("messages", []):
                        st.text(msg)

                st.subheader("🔍 Researcher Findings")
                st.write(final_state.get("findings", "No findings returned."))
                
                st.subheader("💥 PoC Status")
                st.write(final_state.get("poc_status", "PoC step skipped."))
                
                if os.path.exists("ProofOfConcept.py"):
                    st.subheader("📄 ProofOfConcept.py")
                    with open("ProofOfConcept.py", "r") as f:
                        st.code(f.read(), language="python")
                
        except Exception as e:
            st.error("An error occurred:")
            st.exception(e)

st.markdown("---")
st.caption("⚠️ Use responsibly. For educational and authorized testing purposes only.")
