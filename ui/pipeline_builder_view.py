"""InfiniteClaw — DevOps Flow Builder"""
import streamlit as st
import json
from streamlit_agraph import agraph, Node, Edge, Config
from ui.styles import inject_styles
from core.local_db import get_servers, get_current_workspace_id

# Pre-built templates
TEMPLATES = {
    "Custom Flow": [],
    "Standard CI/CD Layout": [
        {"id": "source", "name": "Source Control", "tool": "github_actions", "server": "Unassigned"},
        {"id": "ci", "name": "Jenkins CI", "tool": "jenkins", "server": "Unassigned"},
        {"id": "scan", "name": "Security Scan", "tool": "sonarqube", "server": "Unassigned"},
        {"id": "build", "name": "Container Build", "tool": "docker", "server": "Unassigned"},
        {"id": "deploy", "name": "Deploy", "tool": "kubernetes", "server": "Unassigned"}
    ],
    "AWS 3-Tier Web App": [
        {"id": "dns", "name": "DNS Target", "tool": "aws", "server": "Unassigned"},
        {"id": "lb", "name": "Load Balancer", "tool": "haproxy", "server": "Unassigned"},
        {"id": "web", "name": "Web Proxy", "tool": "nginx", "server": "Unassigned"},
        {"id": "app", "name": "App (EC2)", "tool": "aws", "server": "Unassigned"},
        {"id": "db", "name": "Database (RDS)", "tool": "aws", "server": "Unassigned"}
    ]
}

def mutate_pipeline(action, kwargs):
    """Mutates st.session_state.flow_nodes based on AI requests."""
    nodes = st.session_state.flow_nodes
    if action == "add":
        new_node = {
            "id": kwargs.get("id", f"node_{len(nodes)}"),
            "name": kwargs.get("name", "New Node"),
            "tool": kwargs.get("tool", "docker"),
            "server": "Unassigned"
        }
        after_id = kwargs.get("after_id")
        if after_id:
            idx = next((i for i, n in enumerate(nodes) if n["id"] == after_id), -1)
            if idx != -1:
                nodes.insert(idx + 1, new_node)
            else:
                nodes.append(new_node)
        else:
            nodes.append(new_node)
            
    elif action == "remove":
        target = kwargs.get("id")
        st.session_state.flow_nodes = [n for n in nodes if n["id"] != target]
        
    return f"Pipeline mutated successfully. Current node count: {len(st.session_state.flow_nodes)}"

def render_pipeline_builder():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>🏗️ Interactive Flow Builder</h2>", unsafe_allow_html=True)
    st.markdown("Design your DevOps pipeline architecture on an n8n-style 2D canvas. Chat with the AI to auto-route the graph.")

    if "flow_nodes" not in st.session_state:
        st.session_state.flow_nodes = []

    # Toolbar
    col1, col2 = st.columns([3, 1])
    with col1:
        template = st.selectbox("Select Template", list(TEMPLATES.keys()), label_visibility="collapsed")
        if st.button("Load Template", type="primary"):
            st.session_state.flow_nodes = [dict(n) for n in TEMPLATES[template]]
            st.rerun()
            
    with col2:
        if st.button("🗑️ Clear Canvas"):
            st.session_state.flow_nodes = []
            st.rerun()

    st.markdown("---")
    
    col_graph, col_ai = st.columns([2, 1])
    
    with col_graph:
        st.markdown('### 2D Node Canvas')
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        if not st.session_state.flow_nodes:
            st.info("Your canvas is empty. Select a template or ask the AI to build one!")
        else:
            # Build Agraph Objects
            nodes = []
            edges = []
            
            for i, n in enumerate(st.session_state.flow_nodes):
                nodes.append(
                    Node(id=n["id"], 
                         label=f"{n['name']}\\n[{n['tool']}]", 
                         size=25, 
                         color="#1a202c", 
                         font={'color': 'white', 'size': 14},
                         shape="box"
                    )
                )
                if i > 0:
                    prev = st.session_state.flow_nodes[i-1]
                    edges.append(
                        Edge(source=prev["id"], target=n["id"], width=3, color="#a855f7")
                    )
            
            config = Config(
                width="100%", height=400,
                directed=True, physics=True, hierarchical=True,
                direction="LR", # Left to Right layout like n8n
                nodeHighlightBehavior=True, highlightColor="#00f0ff"
            )
            
            # Render graph
            selected = agraph(nodes=nodes, edges=edges, config=config)
            
            st.caption("You can click and drag nodes to interact with the physics engine.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    with col_ai:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 AI Flow Architect")
        
        if "flow_chat" not in st.session_state:
            st.session_state.flow_chat = [{"role": "assistant", "content": "I can natively wire your architecture together. Tell me to **'Insert SonarQube between CI and Build'** or **'Remove the Web Proxy node'**."}]
            
        # Chat rendering
        chat_container = st.container(height=300)
        with chat_container:
            for msg in st.session_state.flow_chat:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-msg-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    st.markdown(f'<div class="chat-msg-ai">∞ {msg["content"]}</div>', unsafe_allow_html=True)

        flow_input = st.chat_input("Command the graph...")
        if flow_input:
            st.session_state.flow_chat.append({"role": "user", "content": flow_input})
            st.rerun() # Let the next render handle it so user message shows instantly
            
    # LLM Processing State Machine 
    if len(st.session_state.flow_chat) > 1 and st.session_state.flow_chat[-1]["role"] == "user":
        from core.llm_engine import engine
        
        # Tool definition
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "mutate_pipeline",
                    "description": "Modifies the nodes in the UI pipeline graph.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["add", "remove"]},
                            "id": {"type": "string", "description": "A short unique ID like 'sonar1'"},
                            "name": {"type": "string", "description": "Display Name e.g. 'Security Check'"},
                            "tool": {"type": "string", "description": "DevOps tool ID e.g. jenkins, docker, sonarqube, aws"},
                           