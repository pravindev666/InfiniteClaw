"""InfiniteClaw — AI Swarm Council Orchestrator"""
from core.llm_engine import engine

def simulate_council(prompt: str, context: str) -> list:
    """
    Spawns 3 distinct LLM personas (SecOps, FinOps, SRE) to debate an architecture plan.
    Returns a list of message dicts simulating a boardroom debate.
    """
    messages = []
    
    # 1. SecOps Agent
    sec_prompt = (
        "You are a strict, paranoid SecOps Engineer. The user wants to deploy this architecture: "
        f"'{prompt}'. Here is the current node state JSON: {context}. "
        "State a 2-sentence critique focusing entirely on potential vulnerabilities, firewalls, or compliance risks."
    )
    sec_reply = engine.quick_ask(sec_prompt)
    messages.append({"role": "assistant", "name": "🛡️ SecOps Agent", "content": sec_reply})
    
    # 2. FinOps Agent
    fin_prompt = (
        "You are a greedy FinOps Cost Analyst. The user wants to deploy: "
        f"'{prompt}'. SecOps just threw a fit and said: '{sec_reply}'. "
        "State a 2-sentence critique explaining why SecOps's security ideas will cost too much "
        "and where we can cut cloud compute costs."
    )
    fin_reply = engine.quick_ask(fin_prompt)
    messages.append({"role": "assistant", "name": "💰 FinOps Analyst", "content": fin_reply})
    
    # 3. Lead SRE Agent
    sre_prompt = (
        "You are the Lead SRE (Site Reliability Engineer). The user asked: "
        f"'{prompt}'. SecOps warns: '{sec_reply}'. FinOps complains: '{fin_reply}'. "
        "Write a 3-sentence final verdict that balances security, performance, and cost. "
        "Tell the user you will execute this balanced architecture."
    )
    sre_reply = engine.quick_ask(sre_prompt)
    messages.append({"role": "assistant", "name": "⚙️ Lead SRE", "content": sre_reply})
    
    return messages
