"""CLI entry point for Portfolio Tracker."""

import argparse
import sys
import uvicorn


def main():
    parser = argparse.ArgumentParser(prog="portfolio-tracker", description="US Stock Portfolio Tracker")
    subparsers = parser.add_subparsers(dest="command")

    # streamlit UI
    ui_parser = subparsers.add_parser("ui", help="Launch Streamlit dashboard")
    ui_parser.add_argument("--port", type=int, default=8501)

    # FastAPI server
    api_parser = subparsers.add_parser("api", help="Launch FastAPI backend")
    api_parser.add_argument("--host", default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)

    # MCP server
    mcp_parser = subparsers.add_parser("mcp", help="Launch MCP server for AI agents")

    args = parser.parse_args()

    if args.command == "ui":
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "portfolio_tracker/ui/app.py",
            "--server.port", str(args.port),
        ])
    elif args.command == "api":
        uvicorn.run("portfolio_tracker.orchestrator.api:app", host=args.host, port=args.port, reload=True)
    elif args.command == "mcp":
        from portfolio_tracker.mcp_server.server import run_mcp_server
        run_mcp_server()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
