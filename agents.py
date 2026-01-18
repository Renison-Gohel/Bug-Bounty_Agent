import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from tools import (
    list_folders, list_files, view_file, create_file, 
    search_files, regex_search, run_security_audit, terminal_command
)
from dotenv import load_dotenv

load_dotenv()

def get_llm(provider: str, model_name: str, base_url: str = None, api_key: str = None):
    """Factory to create LLM instances based on provider."""
    provider = provider.lower()
    
    if provider == "ollama":
        return ChatOpenAI(
            base_url=base_url or "http://localhost:11434/v1",
            api_key="ollama", # Ollama doesn't need a real key
            model=model_name,
            temperature=0
        )
    elif provider == "openai":
        # OpenAI O1 models do not support temperature=0 (must be 1)
        temp = 1 if model_name.startswith("o1-") else 0
        return ChatOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            model=model_name,
            temperature=temp
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            model=model_name,
            temperature=0
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
            model=model_name,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

# --- Prompts ---
# Note: langgraph.prebuilt.create_react_agent takes a system message string, not a PromptTemplate object for the 'prompt' arg usually, 
# or it manages messages itself. We will pass the instructions as a system message.

researcher_system_message = """You are an expert Security Researcher and Bug Hunter. 
Your goal is to analyze the given Target (URL, IP, Repo, or Directory) and find security vulnerabilities.

You have access to a terminal and file system tools. 
You should:
1. Explore the target (list files, read code, scan ports if IP/URL).
2. Use static analysis tools (like bandit) or manual code review.
3. Use terminal commands (grep, curl, nmap, etc.) to verify findings.
4. Think deeply about potential attack vectors (SQLi, XSS, RCE, IDOR, etc.).

When you have found a vulnerability, provide a detailed description including file paths, code snippets, and why it is vulnerable.
If you have explored the target thoroughly and found NO vulnerabilities, state that clearly and stop. Do not loop indefinitely.
"""

poc_system_message = """You are an expert Exploit Developer and Python Coder.
Your goal is to create a working Proof of Concept (PoC) script in Python (`ProofOfConcept.py`) for a vulnerability found by the Security Researcher.

You should:
1. Understand the vulnerability details provided.
2. Write a Python script (`ProofOfConcept.py`) that reproduces the issue or exploits it.
3. Use `create_file` to save the script.
4. Use `terminal_command` to run the script and verify it works.
5. If it fails, read the error, fix the script, and try again.

When you have successfully created and verified the PoC, confirm it.
If you cannot create a PoC after multiple attempts, explain why and stop.
"""

def create_agents(config: dict):
    """
    Creates agent graphs based on configuration.
    """
    
    # Researcher Setup
    r_conf = config.get("researcher", {})
    r_llm = get_llm(
        r_conf.get("provider", "ollama"),
        r_conf.get("model", "llama3"),
        r_conf.get("base_url"),
        r_conf.get("api_key")
    )
    
    researcher_tools = [
        list_folders, list_files, view_file, 
        search_files, regex_search, run_security_audit, 
        terminal_command
    ]
    
    # create_react_agent returns a CompiledGraph
    researcher_agent = create_react_agent(
        r_llm, 
        researcher_tools, 
        state_modifier=researcher_system_message # Use state_modifier for system prompt in newer langgraph
    )

    # PoC Creator Setup
    p_conf = config.get("poc", {})
    p_llm = get_llm(
        p_conf.get("provider", "ollama"),
        p_conf.get("model", "llama3"),
        p_conf.get("base_url"),
        p_conf.get("api_key")
    )
    
    poc_tools = [create_file, view_file, terminal_command]
    
    poc_agent = create_react_agent(
        p_llm, 
        poc_tools, 
        state_modifier=poc_system_message
    )
    
    return researcher_agent, poc_agent
