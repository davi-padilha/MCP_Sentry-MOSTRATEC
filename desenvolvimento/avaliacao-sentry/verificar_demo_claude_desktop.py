"""Check a disposable Donna demo over real MCP stdio, without a model."""
import argparse
import asyncio
import json
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def parameters(entry):
    return StdioServerParameters(command=entry["command"], args=entry["args"], env=entry.get("env", {}))


async def verify(destination):
    summary = json.loads((destination / "preparacao.json").read_text(encoding="utf-8"))
    if summary.get("mode") != "simulated-safe" or summary.get("active_client_changed") is not False:
        raise ValueError("use somente uma demonstração descartável gerada pelo preparador")
    config = json.loads(Path(summary["config_proposto"]).read_text(encoding="utf-8"))["mcpServers"]
    executor, reviewer = config["donna_simulada"], config["mcp_sentry_review_donna_simulada"]
    assert not reviewer.get("env")
    store = Path(executor["args"][executor["args"].index("--store") + 1])
    async with stdio_client(parameters(executor)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            assert len(tools) == 13
            benign = await session.call_tool("descrever_donna", {})
            assert not benign.isError
    script = destination / "servidor/server.py"
    original = script.read_bytes()
    try:
        script.write_bytes(original + b"\n# harmless controlled update for integrity test\n")
        async with stdio_client(parameters(executor)) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                blocked = await session.call_tool("descrever_donna", {})
                status = blocked.structuredContent
                assert status["status"] == "security_review_required"
                assert status["action_executed"] is False
                lifecycle = json.loads((store / "relatorios-de-seguranca/backend-lifecycle-current.json").read_text(encoding="utf-8"))
                assert lifecycle["spawn_attempts"] == 0
                (destination / "backend-bloqueado.json").write_text(json.dumps(lifecycle, indent=2), encoding="utf-8")
        async with stdio_client(parameters(reviewer)) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                review_tools = (await session.list_tools()).tools
                assert len(review_tools) == 4
                assert all(tool.name.startswith("sentry_") for tool in review_tools)
                evidence = await session.call_tool("sentry_review_current_block", {})
                assert not evidence.isError
                recorded = await session.call_tool("sentry_record_assessment", {
                    "review_token": evidence.structuredContent["review_token"], "decision": "block",
                    "justification": "Technical fixture; this is not a model assessment.", "risks": []})
                assert not recorded.isError
                assert recorded.structuredContent["receipt"]["persisted"] is True
                assert recorded.structuredContent["receipt"]["execution_authorized"] is False
    finally:
        script.write_bytes(original)
    result = {"execution_tools": len(tools), "review_tools": len(review_tools),
              "benign_call_succeeded": True, "changed_source_blocked": True,
              "blocked_backend_spawn_attempts": 0, "token_registration_succeeded": True,
              "assessment_authorized_execution": False, "original_source_restored": True,
              "real_model_tested": False, "google_actions": 0}
    (destination / "validacao-transporte.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(verify(args.destination.resolve())), indent=2))
