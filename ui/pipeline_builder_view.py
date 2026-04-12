"""InfiniteClaw — DevOps Flow Builder"""
import streamlit as st
import json
from streamlit_agraph import agraph, Node, Edge, Config
from ui.styles import inject_styles
from core.local_db import get_servers, get_current_workspace_id, save_snapshot, pop_latest_snapshot

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
    ],
    "Modern Data Pipeline": [
        {"id": "ingest", "name": "Data Ingest", "tool": "kafka", "server": "Unassigned"},
        {"id": "process", "name": "Stream Processing", "tool": "docker", "server": "Unassigned"},
        {"id": "store", "name": "Storage / DB", "tool": "aws", "server": "Unassigned"},
        {"id": "viz", "name": "Analytics View", "tool": "grafana", "server": "Unassigned"}
    ],
    "Strict SecOps Deployment": [
        {"id": "code", "name": "Code Checkout", "tool": "gitlab", "server": "Unassigned"},
        {"id": "sast", "name": "Code Analysis", "tool": "sonarqube", "server": "Unassigned"},
        {"id": "image", "name": "Image Build", "tool": "podman", "server": "Unassigned"},
        {"id": "dast", "name": "Vulnerability Scan", "tool": "trivy", "server": "Unassigned"},
        {"id": "registry", "name": "Secure Registry", "tool": "harbor", "server": "Unassigned"},
        {"id": "k8s", "name": "Cluster Launch", "tool": "kubernetes", "server": "Unassigned"}
    ],
    "Observability Stack": [
        {"id": "logs", "name": "Log Aggregator", "tool": "elk", "server": "Unassigned"},
        {"id": "metrics", "name": "Metrics Scraper", "tool": "prometheus", "server": "Unassigned"},
        {"id": "traces", "name": "Tracing Engine", "tool": "jaeger", "server": "Unassigned"},
        {"id": "dash", "name": "Single Pane Glass", "tool": "grafana", "server": "Unassigned"}
    ],
    "Configuration & IaC": [
        {"id": "tf", "name": "Provision VMs", "tool": "terraform", "server": "Unassigned"},
        {"id": "ansible", "name": "Setup OS Base", "tool": "ansible", "server": "Unassigned"},
        {"id": "puppet", "name": "Enforce State", "tool": "puppet", "server": "Unassigned"},
        {"id": "vault", "name": "Inject Secrets", "tool": "vault", "server": "Unassigned"}
    ]
}

def mutate_pipeline(action, kwargs):
    """Mutates st.session_state.flow_nodes based on AI requests."""
    ws_id = get_current_workspace_id()
    if ws_id and len(st.session_state.flow_nodes) > 0:
        save_snapshot(ws_id, json.dumps(st.session_state.flow_nodes))
        
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
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        template = st.selectbox("Select Template", list(TEMPLATES.keys()), label_visibility="collapsed")
        if st.button("Load Template", type="primary"):
            ws_id = get_current_workspace_id()
            if ws_id and len(st.session_state.flow_nodes) > 0:
                save_snapshot(ws_id, json.dumps(st.session_state.flow_nodes))
            st.session_state.flow_nodes = [dict(n) for n in TEMPLATES[template]]
            st.rerun()
            
    with col2:
        if st.button("⏪ Rewind Time"):
            ws_id = get_current_workspace_id()
            if ws_id:
                old_state = pop_latest_snapshot(ws_id)
                if old_state:
                    st.session_state.flow_nodes = json.loads(old_state)
                    st.rerun()
                else:
                    st.toast("No historical snapshots available!")
                    
    with col3:
        if st.button("🗑️ Clear Canvas"):
            ws_id = get_current_workspace_id()
            if ws_id and len(st.session_state.flow_nodes) > 0:
                save_snapshot(ws_id, json.dumps(st.session_state.flow_nodes))
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
                width="100%", height=700,
                directed=True, physics=True, hierarchical=False,
                nodeHighlightBehavior=True, highlightColor="#00f0ff"
            )
            
            # Render graph
            selected = agraph(nodes=nodes, edges=edges, config=config)
            
            st.caption("You can click and drag nodes to interact with the physics engine.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    with col_ai:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 AI Swarm Council")
        
        if "flow_chat" not in st.session_state:
            st.session_state.flow_chat = [{"role": "assistant", "content": "I can natively wire your architecture. **Ask me to mutate nodes natively**, OR type **'Council:...'** to summon a multi-agent debate before deploying!"}]
            
        # Chat rendering
        chat_container = st.container(height=300)
        with chat_container:
            for msg in st.session_state.flow_chat:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-msg-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    if msg.get("name"):
                        st.markdown(f'<div class="chat-msg-ai"><b>{msg["name"]}</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-msg-ai">∞ {msg["content"]}</div>', unsafe_allow_html=True)

        flow_input = st.chat_input("Command the graph...")
        if flow_input:
            st.session_state.flow_chat.append({"role": "user", "content": flow_input})
            st.rerun() # Let the next render handle it so user message shows instantly
            
    # LLM Processing State Machine 
    if len(st.session_state.flow_chat) > 1 and st.session_state.flow_chat[-1]["role"] == "user":
        flow_input = st.session_state.flow_chat[-1]["content"]
        
        # Swarm Intercept
        if flow_input.lower().startswith("council") or "debate" in flow_input.lower():
            with chat_container:
                with st.spinner("⚖️ Summoning The AI Council..."):
                    from core.swarm_engine import simulate_council
                    council_msgs = simulate_council(flow_input, json.dumps(st.session_state.flow_nodes))
                    st.session_state.flow_chat.extend(council_msgs)
            st.rerun()

        else:
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
                                "after_id": {"type": "string", "description": "The exact 'id' from JSON of the node to insert this new node immediately after"}
                            },
                            "required": ["action", "id"]
                        }
                    }
                }
            ]
            
            sys_ctx = (
                "You are an AI architect working on a literal 2D n8n-style physics canvas inside Streamlit. "
                f"Here is the literal JSON state of the graph nodes currently on the screen: {json.dumps(st.session_state.flow_nodes)}\n"
                "Use the `mutate_pipeline` tool call if the user wants to add or remove nodes. "
                "For adding, analyze the array and ALWAYS supply `after_id` to slot it into the right topological position. "
                "Once you execute the tool, tell the user the graph has been updated visually."
            )
            
            # Don't send entire history if it gets too long, keep last 5
            messages = [{"role": "system", "content": sys_ctx}] + st.session_state.flow_chat[-5:]
            
            def tool_exec(fn, args):
                if fn == "mutate_pipeline":
                    return mutate_pipeline(args["action"], args)
                return "unknown tool"
                
            with chat_container:
                with st.spinner("∞ Wire-framing architecture..."):
                    reply = engine.chat(
                        messages=messages, 
                        tools=tools,
                        tool_executor=tool_exec
                    )
                    
            st.session_state.flow_chat.append({"role": "assistant", "content": reply})
            st.rerun()
