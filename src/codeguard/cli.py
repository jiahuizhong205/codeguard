from __future__ import annotations
import argparse


def main():
    parser = argparse.ArgumentParser(prog="codeguard", description="Coding Agent Harness")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Start the server")
    subparsers.add_parser("init", help="Initialize credentials")
    subparsers.add_parser("credentials", help="Manage credentials")
    subparsers.add_parser("demo", help="Run mechanism demo")

    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn
        from codeguard.server import create_app
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.command == "init":
        print("Initializing CodeGuard...")
        print("This will set up credentials. Use 'codeguard credentials' to manage.")
    elif args.command == "credentials":
        print("Credential management:")
        print("  codeguard credentials status  - Check if configured")
        print("  codeguard credentials store    - Store a key")
        print("  codeguard credentials clear    - Clear a key")
    elif args.command == "demo":
        from codeguard.demo import run_demo
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
