import subprocess
import time
import sys
import os

# Clean Import: Pulling your exact dictionary matrix from util.py
from util import NODE_REGISTRY

# DYNAMIC GENERALIZATION: Loop through all keys, skip 'server', and pull the ports
ports = [value for key, value in NODE_REGISTRY.items() if key != 'server']
print(f"[LAUNCHER] Dynamically extracted ports from NODE_REGISTRY: {ports}")

# Ensure the node_logs directory exists safely before booting up processes
log_dir = "node_logs"
os.makedirs(log_dir, exist_ok=True)

def launch_script(script_name, port=None):
    """Spawns straightforward background processes without process group overhead."""
    cmd = [sys.executable, script_name]
    if port:
        cmd.extend(["--id", str(port)])
        log_file = open(os.path.join(log_dir, f"node_{port}.log"), "w", encoding="utf-8")
        print(f"[LAUNCHER] Starting {script_name} with ID {port} (Logging to node_logs/node_{port}.log)...")
        return subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        
    print(f"[LAUNCHER] Starting {script_name} ...")
    return subprocess.Popen(cmd)

def main():
    processes = []
    log_files = []
    
    try:
        client_script = "client_node.py"
        
        # Step 1: Launch ALL Automated Edge Client Nodes found in the registry dynamically
        for port in ports:
            cmd = [sys.executable, client_script, "--id", str(port)]
            log_file = open(os.path.join(log_dir, f"node_{port}.log"), "w", encoding="utf-8")
            log_files.append(log_file)
            
            print(f"[LAUNCHER] Starting {client_script} with ID {port} (Logging to node_logs/node_{port}.log)...")
            proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
            processes.append(proc)
            
        time.sleep(1.0) # Pause to allow client sockets to bind cleanly

        # Step 2: Launch Core Blockchain TCP Server
        blockchain_server_proc = launch_script("blockchain_server.py")
        processes.append(blockchain_server_proc)
        time.sleep(1.5) # Wait for master ledger engine to boot completely

        # Step 3: Launch Flask Visualization Web Gateway
        app_proc = launch_script("app.py")
        processes.append(app_proc)

        # Generate a clean string of the tracked log files for the terminal output display
        log_file_list = ", ".join([f"node_{p}.log" for p in ports])

        print("\n" + "="*60)
        print("🚀 ALL SYSTEMS ONLINE! Open your browser at: http://127.0.0.1:8080")
        print(f"📁 Tracking Logs dynamically inside: /{log_dir}/")
        print("Press CTRL+C in this terminal to shut down the entire network cleanly.")
        print("="*60 + "\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[LAUNCHER] Terminating background processes...")
        
        # Kill running background processes directly via target handles
        for proc in processes:
            try:
                proc.terminate()
                proc.wait()
            except Exception:
                pass
            
        for file in log_files:
            file.close()
            
        print("[LAUNCHER] All network tasks stopped cleanly.")

if __name__ == "__main__":
    main()
