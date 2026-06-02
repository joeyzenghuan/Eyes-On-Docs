# EyesOnDocs - Codex Project Guide

## Project Overview

Doc Update Notification Bot - monitors Microsoft documentation updates and sends notifications. Includes a Python backend, Next.js frontend, and MCP server.

## Repository

- GitHub: joeyzenghuan/Eyes-On-Docs
- Main branch: `main`, working branch: `master`

## Production VM

- Credentials: `.Codex/vm_credentials.env` (not committed to git)
- Connect via tmux session `eyesondocs`, window `remote`

## Skills

- **[Deploy to VM](.Codex/skills/deploy-vm.md)**: Full deployment guide including git sync, config upload, backend/frontend/MCP server restart

## Key Paths (VM)

| Component | Path |
|---|---|
| Project root | `/home/joey/DocUpdateNotificationBot` |
| Frontend | `/home/joey/DocUpdateNotificationBot/web` |
| MCP Server | `/home/joey/DocUpdateNotificationBot/mcp_server` |
| Config | `/home/joey/DocUpdateNotificationBot/target_config.json` |

## Key Paths (Local macOS)

| Component | Path |
|---|---|
| Project root | `/Users/joey/gitrepo/DocUpdateNotificationBot2/DocUpdateNotificationBot` |
| Config files | `logs/target_config-*.json` |
