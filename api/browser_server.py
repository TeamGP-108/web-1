import asyncio
import sys
import subprocess
import os
import socket

def get_local_ip():
    """Detects the local IP address of the machine."""
    try:
        # Connect to a public DNS server to determine the outgoing interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

async def run_server():
    print("\n" + "="*50)
    print("PLAYWRIGHT REMOTE BROWSER SERVER")
    print("="*50)
    
    local_ip = get_local_ip()
    print(f"Starting browser server on {local_ip} (Port 4000)...", flush=True)
    
    try:
        # We use a custom environment variable to force Firefox
        env = os.environ.copy()
        env["BROWSER"] = "firefox" 
        env["PLAYWRIGHT_BROWSER"] = "firefox"
        
        # Use a fixed port (4000) and allow external connections (--host 0.0.0.0)
        cmd = [sys.executable, "-m", "playwright", "run-server", "--port", "4000", "--host", "0.0.0.0"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        print("Waiting for WebSocket URL...", flush=True)
        
        ws_endpoint = None
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line_str = line.decode().strip()
            
            if "ws://" in line_str:
                # CLI output might be "Listening on ws://0.0.0.0:4000/..."
                # We need to extract the URL and replace 0.0.0.0 with the LAN IP
                parts = line_str.split("ws://")
                raw_url_part = parts[1].strip()
                
                # Replace 0.0.0.0 or localhost with actual LAN IP for the user to copy
                if raw_url_part.startswith("0.0.0.0"):
                    final_url = raw_url_part.replace("0.0.0.0", local_ip, 1)
                elif raw_url_part.startswith("127.0.0.1"):
                    final_url = raw_url_part.replace("127.0.0.1", local_ip, 1)
                elif raw_url_part.startswith("localhost"):
                    final_url = raw_url_part.replace("localhost", local_ip, 1)
                else:
                    final_url = raw_url_part
                    
                ws_endpoint = "ws://" + final_url
                break
                
        if ws_endpoint:
            print(f"\n🚀 SERVER IS LIVE!", flush=True)
            print(f"WebSocket URL: {ws_endpoint}", flush=True)
            print(f"\n[!] IMPORTANT: Make sure Port 4000 is allowed in your firewall.", flush=True)
            print("Copy the URL above and paste it into your 'config.py' file under BROWSER_WS_URL.", flush=True)
            print("Keep this terminal open while using the automation.", flush=True)
            print("="*50 + "\n", flush=True)
            
            await process.wait()
        else:
            print("Error: Could not find WebSocket URL in server output.", flush=True)
            
    except Exception as e:
        print(f"Error starting server: {e}", flush=True)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
