"""
InfiniteClaw — Server Scanner
Runs all 30 tool adapters' detect() against a server in parallel.
"""
import concurrent.futures
from typing import Dict, List
from core.ssh_manager import ssh_manager
from core.local_db import upsert_server_tool, update_server_last_scan
from core.activity_feed import log_event
from tools.tool_router import tool_router


def scan_server(server_id: str) -> List[Dict]:
    """
    Scan a server for all 30 DevOps tools using ThreadPoolExecutor.
    Returns list of {tool_name, status, version, port, extra_info}.
    """
    try:
        ssh_conn = ssh_manager.get_connection(server_id)
    except Exception as e:
        log_event("scan_error", f"Cannot connect to server {server_id}: {e}", server_id=server_id)
        return []

    results = []

    def _detect_tool(adapter):
        try:
            detection = adapter.detect(ssh_conn)
            return {
                "tool_name": adapter.name,
                "display_name": adapter.display_name,
                "icon": adapter.icon,
                "category": adapter.category,
                "status": detection.status.value,
                "status_icon": detection.status.icon,
                "version": detection.version,
                "port": detection.port,
                "extra_info": detection.extra_info,
            }
        except Exception as e:
            return {
                "tool_name": adapter.name,
                "display_name": adapter.display_name,
                "icon": adapter.icon,
                "category": adapter.category,
                "status": "error",
                "status_icon": "❌",
                "version": None,
                "port": None,
                "extra_info": {"error": str(e)},
            }

    # Run detection in parallel (max 10 threads)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_detect_tool, adapter): adapter.name
            for adapter in tool_router.get_all_adapters().values()
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

            # Persist to DB
            upsert_server_tool(
                server_id=server_id,
                tool_name=result["tool_name"],
                status=result["status"],
                version=result.get("version"),
                port=result.get("port"),
                extra_info=result.get("extra_info"),
            )

    # Update last scan timestamp
    update_server_last_scan(server_id)

    # Log summary
    installed = [r for r in results if r["status"] not in ("not_installed", "error")]
    log_event(
        "scan_complete",
        f"Scan complete: {len(installed)}/{len(results)} tools detected",
        server_id=server_id
    )

    # Sort by category then name
    results.sort(key=lambda x: (x["category"], x["tool_name"]))
    return results


def get_detected_tools_for_display(server_id: str) -> Dict[str, List[Dict]]:
    """Get tools grouped by category for sidebar display."""
    from core.local_db import get_server_tools
    tools = get_server_tools(server_id)

    grouped = {}
    for t in tools:
        adapter = tool_router.get_adapter(t["tool_name"])
        if not adapter:
            continue
        cat = adapter.category
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "name": adapter.name,
            "display_name": adapter.display_name,
            "icon": adapter.icon,
            "status": t["status"],
            "version": t.get("version"),
            "port": t.get("port"),
        })

    return grouped
