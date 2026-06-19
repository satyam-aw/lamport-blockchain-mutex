import subprocess
import time
import sys
import os

# Clean Import: Pulling your exact dictionary matrix from util.py
from util import NODE_REGISTRY

# DYNAMIC GENERALIZATION: Loop through all keys, skip 'server', and pull the ports
node_ids = [key for key, value in NODE_REGISTRY.items() if key != 'server']
log_files = []
print(f"[LAUNCHER] Dynamically extracted IDs from NODE_REGISTRY: {node_ids}")

# Ensure the node_logs directory exists safely before booting up processes
log_dir = "node_logs"
os.makedirs(log_dir, exist_ok=True)

def launch_script(script_name, node_id=None):
    """Spawns straightforward background processes without process group overhead."""
    cmd = [sys.executable, script_name]
    if node_id:
        cmd.extend(["--id", str(node_id)])
        log_file = open(os.path.join(log_dir, f"node_{node_id}.log"), "w", encoding="utf-8")
        log_files.append(log_file)
        print(f"[LAUNCHER] Starting {script_name} with ID {node_id} (Logging to node_logs/node_{node_id}.log)...")
        return subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
    else:   
        print(f"[LAUNCHER] Starting {script_name} ...")
        return subprocess.Popen(cmd)

def main():
    processes = []
    
    try:
        client_script = "client_node.py"
        
        # Step 1: Launch ALL Automated Edge Client Nodes found in the registry dynamically
        for id in node_ids:
            proc = launch_script(client_script, id)
            processes.append(proc)
            time.sleep(0.3) # Pause to allow client sockets to bind cleanly
            

        # Step 2: Launch Core Blockchain TCP Server
        blockchain_server_proc = launch_script("blockchain_server.py")
        processes.append(blockchain_server_proc)
        time.sleep(1.5) # Wait for master ledger engine to boot completely

        # Step 3: Launch Flask Visualization Web Gateway
        app_proc = launch_script("app.py")
        processes.append(app_proc)

        # Generate a clean string of the tracked log files for the terminal output display
        log_file_list = ", ".join([f"node_{p}.log" for p in node_ids])

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
