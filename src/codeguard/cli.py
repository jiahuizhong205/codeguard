from __future__ import annotations
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(prog="codeguard", description="Coding Agent Harness")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Start the server")
    subparsers.add_parser("init", help="Create .env config file")
    subparsers.add_parser("credentials", help="Manage credentials")
    subparsers.add_parser("demo", help="Run mechanism demo")

    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn
        from codeguard.server import create_app
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.command == "init":
        _init_config()
    elif args.command == "credentials":
        from codeguard.config import is_configured, LLM_BASE_URL, LLM_MODEL
        print(f"  Configured: {is_configured()}")
        print(f"  Base URL:  {LLM_BASE_URL or '(not set)'}")
        print(f"  Model:     {LLM_MODEL}")
        print(f"\n  Edit .env to change settings.")
    elif args.command == "demo":
        from codeguard.demo import run_demo
        run_demo()
    else:
        parser.print_help()


def _init_config():
    import getpass

    env_path = Path(".env")
    if env_path.exists():
        print(".env already exists. Edit it directly to change settings.")
        return

    print("=== CodeGuard 初始化 ===\n")
    base_url = input("LLM API 地址 (OpenAI 兼容): ").strip()
    api_key = getpass.getpass("API Key (隐藏输入): ").strip()
    model = input("模型名称 (默认 gpt-4): ").strip() or "gpt-4"

    content = f"""LLM_BASE_URL={base_url}
LLM_API_KEY={api_key}
LLM_MODEL={model}
"""
    env_path.write_text(content, encoding="utf-8")
    print(f"\n.env 已创建: {env_path.resolve()}")
    print("运行 codeguard serve 启动服务。")


if __name__ == "__main__":
    main()
