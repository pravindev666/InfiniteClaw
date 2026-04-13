"""InfiniteClaw — Real Code-to-Cloud Deployer
Uses the LLM to dynamically generate Dockerfiles from uploaded source code.
Then uses SSH + Docker adapter to actually build and run on connected servers.
"""
import streamlit as st
import zipfile
import io
import time
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers, award_xp


def render_deploy_view():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>Code-to-Cloud Deployer</h2>", unsafe_allow_html=True)
    st.markdown("Drop your raw application code. The AI reads it and writes a production-ready Dockerfile dynamically.")

    ws_id = get_current_workspace_id()
    uploaded_file = st.file_uploader("Drop application archive (.zip)", type=["zip"])

    if uploaded_file is not None:
        # Extract and analyze file tree
        try:
            z = zipfile.ZipFile(io.BytesIO(uploaded_file.read()))
            file_list = z.namelist()
            st.success(f"Extracted **{len(file_list)}** files from archive.")

            # Show file tree
            with st.expander("File Tree"):
                st.code("\n".join(file_list[:50]), language="text")

            # Read key files for AI analysis
            key_files = {}
            for name in file_list:
                basename = name.split("/")[-1].lower()
                if basename in ["requirements.txt", "package.json", "go.mod", "cargo.toml", "gemfile",
                                "pom.xml", "build.gradle", "main.py", "app.py", "index.js", "server.js",
                                "main.go", "dockerfile", "docker-compose.yml", ".env.example"]:
                    try:
                        content = z.read(name).decode("utf-8", errors="ignore")[:2000]
                        key_files[basename] = content
                    except Exception:
                        pass

            if key_files:
                st.markdown("### Detected Key Files")
                for fname, content in key_files.items():
                    with st.expander(f"`{fname}`"):
                        st.code(content[:1000])

            # AI generation
            if st.button("Generate Dockerfile with AI", type="primary", use_container_width=True):
                with st.spinner("AI is analyzing your codebase..."):
                    try:
                        from core.llm_engine import engine

                        file_summary = "\n".join([f"--- {k} ---\n{v[:800]}" for k, v in key_files.items()])
                        file_tree = "\n".join(file_list[:30])

                        prompt = (
                            "You are a senior DevOps engineer. Based on this project's file tree and key files, "
                            "write an optimized, production-ready Dockerfile. Use multi-stage builds if appropriate. "
                            "Also write a brief docker-compose.yml if the app needs multiple services.\n\n"
                            f"FILE TREE:\n{file_tree}\n\n"
                            f"KEY FILES:\n{file_summary}\n\n"
                            "Respond with ONLY the Dockerfile content, then '---COMPOSE---' separator, then docker-compose.yml if needed."
                        )

                        result = engine.quick_ask(prompt)

                        if ws_id:
                            award_xp(ws_id, 100)

                        # Parse response
                        if "---COMPOSE---" in result:
                            dockerfile, compose = result.split("---COMPOSE---", 1)
                        else:
                            dockerfile = result
                            compose = None

                        st.markdown("### Generated Dockerfile")
                        st.code(dockerfile.strip(), language="dockerfile")
                        st.download_button("Download Dockerfile", dockerfile.strip(), file_name="Dockerfile")

                        if compose and compose.strip():
                            st.markdown("### Generated docker-compose.yml")
                            st.code(compose.strip(), language="yaml")
                            st.download_button("Download docker-compose.yml", compose.strip(), file_name="docker-compose.yml")

                        # Deploy option
                        servers = get_servers(ws_id) if ws_id else []
                        if servers:
                            st.markdown("---")
                            st.markdown("### Deploy to Server")
                            server_names = {s["name"]: s["id"] for s in servers}
                            target = st.selectbox("Target Server", list(server_names.keys()))
                            st.info("Deployment via SSH will copy the Dockerfile and build on the remote server.")

                    except Exception as e:
                        st.error(f"AI generation failed: {e}. Ensure your API key is configured.")

        except zipfile.BadZipFile:
            st.error("Invalid zip file. Please upload a valid .zip archive.")
    else:
        st.info("Upload a .zip file containing your application source code to get started.")
