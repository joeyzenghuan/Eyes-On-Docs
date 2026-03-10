# Skill: Deploy to VM

Deploy the latest code to the production VM. Includes syncing git, replacing config, restarting Python backend, rebuilding frontend, and restarting MCP server.

## Prerequisites

- VM credentials stored in `.claude/vm_credentials.env`
- tmux session `eyesondocs` must exist locally
- `sshpass` installed on macOS (`brew install sshpass`)

## Step 1: Connect to VM via tmux

Create a tmux window and SSH into the VM:

```bash
# Create a new window in existing tmux session
tmux new-window -t eyesondocs -n remote

# SSH into VM
tmux send-keys -t eyesondocs:remote "ssh joey@<VM_HOST>" Enter
# Wait for password prompt (~3s)
sleep 3
tmux send-keys -t eyesondocs:remote "<VM_PASSWORD>" Enter
# Wait for login (~3s)
sleep 3

# Verify login
tmux capture-pane -t eyesondocs:remote -p -S -5
```

## Step 2: Sync Git repo on VM

```bash
tmux send-keys -t eyesondocs:remote "cd /home/joey/DocUpdateNotificationBot" Enter
tmux send-keys -t eyesondocs:remote "git pull origin master" Enter
# Wait ~5s for pull to complete
sleep 5
tmux capture-pane -t eyesondocs:remote -p -S -10
```

## Step 3: Upload target_config.json (if needed)

Use `scp` from local macOS to replace config on VM:

```bash
sshpass -p '<VM_PASSWORD>' scp -o StrictHostKeyChecking=no \
  /Users/joey/gitrepo/DocUpdateNotificationBot2/DocUpdateNotificationBot/logs/<config_file> \
  joey@<VM_HOST>:/home/joey/DocUpdateNotificationBot/target_config.json
```

Verify on VM:
```bash
tmux send-keys -t eyesondocs:remote "ls -la target_config.json" Enter
```

## Step 4: Restart Python backend (eyes_on_docs.py)

```bash
# Kill existing process
tmux send-keys -t eyesondocs:remote "pkill -f eyes_on_docs.py" Enter
sleep 2

# Verify killed
tmux send-keys -t eyesondocs:remote "ps aux | grep eyes_on_docs.py" Enter
sleep 1

# Start with nohup (must be in project dir)
tmux send-keys -t eyesondocs:remote "cd /home/joey/DocUpdateNotificationBot" Enter
tmux send-keys -t eyesondocs:remote "nohup python3 eyes_on_docs.py &" Enter
sleep 3

# Verify running
tmux send-keys -t eyesondocs:remote "ps aux | grep eyes_on_docs.py" Enter
sleep 1
tmux capture-pane -t eyesondocs:remote -p -S -5
```

## Step 5: Rebuild and restart frontend (Next.js)

```bash
tmux send-keys -t eyesondocs:remote "cd /home/joey/DocUpdateNotificationBot/web" Enter

# Install dependencies
tmux send-keys -t eyesondocs:remote "npm install" Enter
# Wait ~60s for npm install
sleep 60
tmux capture-pane -t eyesondocs:remote -p -S -5

# Build
tmux send-keys -t eyesondocs:remote "npm run build" Enter
# Wait ~60s for build
sleep 60
tmux capture-pane -t eyesondocs:remote -p -S -20

# Restart with pm2
tmux send-keys -t eyesondocs:remote "pm2 restart eyesondocs" Enter
sleep 3
tmux capture-pane -t eyesondocs:remote -p -S -10

# Check logs
tmux send-keys -t eyesondocs:remote "pm2 logs eyesondocs --lines 20" Enter
sleep 5
tmux capture-pane -t eyesondocs:remote -p -S -30
```

## Step 6: Restart MCP server

```bash
# Kill existing process (may need kill -9 if pkill doesn't work)
tmux send-keys -t eyesondocs:remote "pkill -f eyesondocs_mcp_server_http_search_fetch.py" Enter
sleep 2
tmux send-keys -t eyesondocs:remote "ps aux | grep eyesondocs_mcp_server_http_search_fetch" Enter
# If still alive, use: kill -9 <PID>

# Start from git project's mcp_server directory
tmux send-keys -t eyesondocs:remote "cd /home/joey/DocUpdateNotificationBot/mcp_server" Enter
tmux send-keys -t eyesondocs:remote "nohup python3 eyesondocs_mcp_server_http_search_fetch.py &" Enter
sleep 3

# Verify running
tmux send-keys -t eyesondocs:remote "ps aux | grep eyesondocs_mcp_server_http_search_fetch" Enter
sleep 1
tmux capture-pane -t eyesondocs:remote -p -S -5
```

## Step 7: Verify all services

```bash
tmux send-keys -t eyesondocs:remote "ps aux | grep -E 'eyes_on_docs|eyesondocs_mcp_server|node.*recipe'" Enter
sleep 1
tmux capture-pane -t eyesondocs:remote -p -S -10
```

## Tips

- Always use `tmux capture-pane -t eyesondocs:remote -p -S -<N>` to read output (N = lines of history)
- For long commands (npm install/build), wait 30-60s before capturing
- If `pkill` doesn't kill a process, use `kill -9 <PID>`
- The frontend runs on port 10086 via pm2
- The Python backend uses `nohup` + background `&`
- The MCP server also uses `nohup` + background `&`

## Services Summary

| Service | Directory | Start Command | Manage |
|---|---|---|---|
| eyes_on_docs.py | /home/joey/DocUpdateNotificationBot | `nohup python3 eyes_on_docs.py &` | `pkill -f eyes_on_docs.py` |
| MCP Server | /home/joey/DocUpdateNotificationBot/mcp_server | `nohup python3 eyesondocs_mcp_server_http_search_fetch.py &` | `pkill -f eyesondocs_mcp_server_http_search_fetch.py` |
| Frontend (Next.js) | /home/joey/DocUpdateNotificationBot/web | `pm2 restart eyesondocs` | `pm2 logs eyesondocs` |
| TTS Gradio | /home/joey | `nohup python3 tts_gradio_yield.py &` | `pkill -f tts_gradio_yield.py` |
| Image Generator | /home/joey | `nohup python3 image_generator_ui_password.py &` | `pkill -f image_generator_ui_password.py` |
