# How InfiniteClaw Orchestrates (Technical Visuals)

Since we are pushing the boundaries of "Alpha-Mode," understanding the internal orchestration is key. Here are the professional technical infographics (via Mermaid) that explain the "How" of this project.

## 1. The Command Chain (Macro-Architecture)
This diagram explains how a natural language prompt becomes a live infrastructure action.

```mermaid
graph LR
    User([User Prompt]) --> NLP[AI Intent Parser]
    NLP --> Router{Tool Router}
    Router -->|Selects| Adapter[31+ Tool Adapters]
    Adapter -->|Constructs| Cmd[Remote Command]
    Cmd --> SSH[SSH Connection Pool]
    SSH -->|Executes| Target[Target Infrastructure]
    Target -- Result --> Adapter
    Adapter -- Insights --> User
```

## 2. Alpha-Mode: The Autonomous Healing Loop
How InfiniteClaw moves from a dashboard to an autonomous "SRE-Watcher."

```mermaid
graph TD
    Monitor[SRE-Watcher Daemon] -->|Pings| Cluster[Production Cluster]
    Cluster -- Error 502 --> Monitor
    Monitor -->|Alerts| Core[Alpha-Mode Brain]
    Core -->|Reasons| Swarm[AI Swarm Council]
    Swarm -->|Decides| Plan[Remediation Plan]
    Plan -->|Auto-Heal| Cluster
    Plan -->|Notifies| User[Telegram Bot]
```

## 3. Secure Bridge: The "Bastion" Flow
How we maintain Zero-Trust principles without exposing root SSH keys to AI agents.

```mermaid
sequenceDiagram
    participant User as Remote Dev
    participant TG as Telegram Bot
    participant Vault as Encrypted Vault
    participant SSH as SSH Manager
    participant Srv as Remote Server
    
    User->>TG: "Show me Nginx logs"
    TG->>Vault: Fetch Session Secret
    Vault->>SSH: Authorize Temp Connection
    SSH->>Srv: Run 'tail -n 100 /var/log/nginx/error.log'
    Srv-->>SSH: Return Raw Logs
    SSH->>TG: Format & Redact Secrets
    TG-->>User: Secure Log Stream
```

> [!TIP]
> **Pro-Tip**: You can copy these diagrams directly into any Markdown document (like GitHub or Notion) and they will render as professional, high-contrast infographics!

---
*Created by the InfiniteClaw Alpha-Mode Architect.*
