<div align="center">

<img src="static/img/infiniteclaw-logo.png" alt="InfiniteClaw" width="200"/>

# ∞ InfiniteClaw

### AI-Powered DevOps Infrastructure Management Platform

**One Claw To Rule Them All. Infinite Reach. Total Control.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-AI%20Engine-00f0ff?style=for-the-badge)](https://litellm.ai)
[![Tools](https://img.shields.io/badge/DevOps%20Tools-31-a855f7?style=for-the-badge)](https://github.com)

</div>

---

## 📋 Project Description

**InfiniteClaw** is a **local-first, AI-powered DevOps infrastructure management platform** that connects to your remote servers via SSH and provides unified control over 31 enterprise DevOps tools through a single, intelligent dashboard.

It combines the power of **Large Language Models (OpenAI GPT-4, Claude, Gemini)** with real-time **SSH-based server management** to create an AI assistant that can detect, monitor, configure, and control your entire DevOps toolchain — from Jenkins pipelines to Kubernetes clusters, from Docker containers to Terraform infrastructure.

> **Project Domain:** AI-Assisted DevOps Automation & Infrastructure Management  
> **Academic Topic:** Intelligent Infrastructure Orchestration using LLM-Driven Agentic Systems  
> **Category:** Cloud Computing & DevOps | Artificial Intelligence | Systems Administration

### Key Innovation
Unlike traditional DevOps dashboards that require manual configuration for each tool, InfiniteClaw uses **AI-driven auto-detection** — it scans your servers, discovers installed tools automatically, and provides contextual AI assistance for each one. You can ask natural language questions like *"Show me all failed Jenkins builds"* or *"Scale the Kubernetes deployment to 5 replicas"* and the AI executes the appropriate commands.

---

## ∞ Features

| Feature | Description |
|---|---|
| 🧠 **AI-Powered Chat** | Natural language control of your infrastructure using OpenAI/Claude/Gemini via LiteLLM |
| 🔍 **Auto-Detection** | Parallel scanning of servers to discover 31 DevOps tools automatically |
| 📺 **Pictorial GUI** | Live dashboards with real-time data for every detected tool |
| 💬 **Context-Aware AI** | Each tool gets its own AI chatbox that understands the tool's context |
| 🔄 **CI/CD Visualization** | Pipeline flow view — trace code from push to deployment |
| 📱 **Telegram Control** | Manage infrastructure remotely from your phone |
| 🖥️ **Desktop App** | Native window via PyWebView — runs like a desktop application |
| 🔒 **100% Local** | No cloud dependencies — runs entirely on your machine |
| 🔑 **Multi-Server SSH** | Manage unlimited servers with connection pooling |
| 📊 **Usage Analytics** | Track AI token usage, costs, and response times |

---

## 🔧 Supported Tools (31)

| Category | Tools | Count |
|---|---|---|
| 🏗️ **CI/CD** | Jenkins, GitLab CI, ArgoCD, GitHub Actions | 4 |
| 🐳 **Containers** | Docker, Kubernetes, Helm, Podman, Harbor Registry | 5 |
| 📡 **Monitoring** | Prometheus, Grafana, Splunk, ELK Stack, Nagios, Jaeger, Zabbix | 7 |
| ⚙️ **Config & IaC** | Ansible, Terraform, Chef, Puppet, Packer, HashiCorp Vault, Consul | 7 |
| 🛡️ **Security** | SonarQube, Trivy | 2 |
| 🌐 **Networking** | Nginx, HAProxy, Traefik | 3 |
| 📦 **Data & Messaging** | Kafka, RabbitMQ, Nexus Artifactory | 3 |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API Key (or any LiteLLM-supported provider)
- SSH access to at least one remote server

### Installation

```bash
# Clone the project
cd InfiniteClaw

# Install dependencies
pip install -r requirements.txt

# First-time setup (creates account, configures API key, adds server)
python cli.py setup
```

### Launch Options

```bash
# Option 1: Streamlit Web UI
streamlit run app.py

# Option 2: Desktop App (native window)
python desktop_launcher.py

# Option 3: Terminal Chat
python cli.py chat

# Option 4: Telegram Bot
python channels/telegram_worker.py
```

---

## 🖥️ CLI Commands

```bash
python cli.py setup          # First-time setup wizard
python cli.py status         # Infrastructure health check
python cli.py chat           # Interactive AI chat in terminal
python cli.py scan <server>  # Scan server for DevOps tools
python cli.py server list    # List connected servers
python cli.py server add     # Add a new SSH server
```

---

## 🏗️ Architecture

```
InfiniteClaw/
├── app.py                  # Streamlit Web UI entry point
├── cli.py                  # Typer CLI interface
├── desktop_launcher.py     # Native desktop window (PyWebView)
├── SOUL.md                 # AI personality directive
│
├── core/                   # Engine & Infrastructure
│   ├── config.py           # Configuration & API key management
│   ├── local_db.py         # SQLite database (10 tables)
│   ├── llm_engine.py       # LLM orchestration via LiteLLM
│   ├── ssh_manager.py      # Multi-server SSH connection pooling
│   ├── vault.py            # PBKDF2-encrypted secret storage
│   ├── activity_feed.py    # Real-time event logging
│   └── metrics.py          # Usage analytics tracking
│
├── tools/                  # 31 DevOps Tool Adapters
│   ├── base.py             # Abstract adapter interface
│   ├── tool_router.py      # Master routing engine
│   ├── scanner.py          # Parallel server scanner
│   └── *_adapter.py        # Individual tool adapters (31 files)
│
├── ui/                     # Streamlit Views
│   ├── styles.py           # Glassmorphic CSS theme
│   ├── views.py            # Main dispatcher & sidebar
│   ├── dashboard_view.py   # Infrastructure overview
│   ├── devops_tool_view.py # Generic tool page (GUI + AI chat)
│   ├── server_view.py      # SSH server management
│   ├── chat_view.py        # General AI chat
│   └── workflow_view.py    # CI/CD pipeline visualization
│
├── channels/               # Communication Channels
│   └── telegram_worker.py  # Telegram bot interface
│
└── static/img/             # Assets
    └── infiniteclaw-logo.png
```

---

## 🔄 How It Works

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   User       │────▶│  AI Engine   │────▶│  Tool Router  │
│  (UI/CLI/TG) │     │  (LiteLLM)   │     │  (31 adapters)│
└─────────────┘     └──────────────┘     └───────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  SSH Manager   │
                                          │  (Paramiko)    │
                                          └───────┬───────┘
                                                  │
                              ┌────────────┬──────┴──────┬────────────┐
                              ▼            ▼             ▼            ▼
                         Server 1     Server 2      Server 3     Server N
                         Jenkins      Docker        Prometheus    Terraform
                         Nginx        K8s           Grafana       Ansible
```

1. **You ask** → "Show me failed Jenkins builds on prod-server"
2. **AI Engine** → Parses intent, selects Jenkins adapter
3. **Tool Router** → Routes to `jenkins_adapter.execute_tool_call()`
4. **SSH Manager** → Executes `curl localhost:8080/api/json` on prod-server
5. **AI responds** → Formatted results with analysis

---

## 📞 Technologies Used

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| AI Engine | LiteLLM (OpenAI, Claude, Gemini, DeepSeek) |
| Web UI | Streamlit |
| Desktop App | PyWebView |
| CLI | Typer + Rich |
| SSH | Paramiko |
| Database | SQLite |
| Encryption | Cryptography (PBKDF2) |
| Telegram | python-telegram-bot |
| Server | FastAPI + Uvicorn |

---

## 📄 License

MIT License — Built with ∞ by InfiniteClaw
