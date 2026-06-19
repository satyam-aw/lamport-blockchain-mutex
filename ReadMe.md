# Decentralized Blockchain Network and Chandy-Lamport Snapshot Simulation

A high-fidelity academic platform simulating a decentralized blockchain consensus network. This system decouples asynchronous web visualization overlays from the underlying synchronous Remote Procedure Call (RPC) network layer. The framework models state replication, automated transaction serialization, linear ledger auditability, and dynamic fault isolation. 

Crucially, the architecture utilizes the **Chandy-Lamport Distributed Snapshot Algorithm** to capture consistent global states across asynchronous nodes without suspending real-time transaction processing.

## Video Demonstration

[![Watch the Simulation](https://img.youtube.com/vi/0dgBuVx6GFQ/maxresdefault.jpg)](https://youtu.be/0dgBuVx6GFQ)

*Click the image above to watch a walk-through of the distributed synchronization execution space and telemetry dashboard dashboard.*

---

## Core Consensus & Distributed State Synchronization

### The Chandy-Lamport Snapshot Algorithm
To verify ledger integrity and audit node states across the network without halting execution, the framework implements a strict variant of the **Chandy-Lamport Distributed Snapshot Algorithm**. 

* **Marker Propagation:** When a global state audit or validation check is triggered via the presentation gateway, a control message (`Marker`) is injected into the network via `blockchain_server.py`.
* **Local State Capture:** Upon receiving the `Marker` for the first time, an edge client node instantly records its internal state (including its local blockchain copy and ledger balances) and begins tracking incoming transaction channels.
* **Channel State Recording:** The node records incoming messages on all adjacent channels until it receives a matching `Marker` from each inbound connection. This ensures a cryptographically verifiable, consistent global snapshot is achieved, preventing anomalies such as double-spending or orphan blocks during network transmission delays.

---

## Architectural Topology and Communication Protocol

To eliminate performance degradation (such as I/O blocking or thread starvation) caused by computationally intensive operations like Proof-of-Work (PoW) mining, the architecture enforces a strict separation of concerns across three micro-architectural tiers:

### 1. Presentation & Gateway Layer (`app.py` ➔ Port 8080)
* Hosts a non-blocking HTTP and WebSocket daemon managed by the `Flask-SocketIO` engine wrapper.
* Serves the event-driven HTML5 telemetry dashboard interface and manages a stateful client pipeline via Engine.IO v4.
* Intercepts asynchronous browser events and serializes them before forwarding payloads to the underlying consensus layers over raw TCP.

### 2. Coordination & Master Control Layer (`blockchain_server.py` ➔ Port 5000)
* Functions as the central backbone network listener utilizing primitive BSD raw TCP stream sockets (`SOCK_STREAM`).
* Manages the volatile, centralized transaction buffer (`queue = []`) and computes ledger asset states on-demand via O(N) linear traversal.
* Spawns upstream push-only Socket.IO client instances to mirror transaction processing, balance changes, and Chandy-Lamport global state results directly to the 8080 gateway.

### 3. Distributed Compute Consensus Clusters (`client_node.py` ➔ Dynamic Registry Ports)
* Models autonomous verification nodes executing independent state ledger changes.
* Continuously monitor local TCP ports assigned via the global registry layout to compute transaction bounds, manage local message queues, and handle cryptographic validation sweeps.

---

## Matrix-Driven Process Lifecycle Management

The execution space relies on a generalized, cross-platform controller script (`run_network.py`) that abstracts operating system discrepancies between native Windows (Win32) environments and Linux environments like the Windows Subsystem for Linux (WSL).

### Topology Mapping via `NODE_REGISTRY`
The network layout avoids hardcoded configurations by dynamically bootstrapping itself from the central matrix inside `util.py`:

```python
# Sample Configuration inside util.py
NODE_REGISTRY = {
    'server': server_addr,       # Master Engine Endpoint Binding
    '1': (default_ip, 7001),     # Distributed Cluster Node 1
    '2': (default_ip, 7002),     # Distributed Cluster Node 2
    '3': (default_ip, 7003),     # Distributed Cluster Node 3
}
```

The orchestration engine (`run_network.py`) processes this environment schema automatically:
* **Dynamic Key Discovery:** Loops through all active keys inside `NODE_REGISTRY`, dynamically skipping the `'server'` definition to isolate and spawn edge compute nodes.
* **I/O Redirection & Isolation:** Spawns independent background processes using `subprocess.Popen`. It redirects each client node's standard output (`stdout`) and standard error (`stderr`) streams into isolated `.log` files cached in the `/node_logs/` sub-directory.
* **Deterministic Socket Reclamation:** Catches SIGINT (`KeyboardInterrupt` / `Ctrl+C`) and gracefully terminates each background subprocess PID sequentially across platforms, ensuring zero ghost processes remain to lock system network sockets.

---

## System Inventory & Verification Workflow

```text
📁 (root)/
│
├── 📄 run_network.py          # Cross-platform multi-process orchestration module
├── 📄 blockchain_server.py    # Master ledger controller daemon (State Machine)
├── 📄 app.py                  # Asynchronous HTTP/WebSocket middleware gateway
├── 📄 client_node.py          # Edge cluster compute node and consensus validator
├── 📄 blockchain.py           # Cryptographic engine (SHA-256 / Proof-of-Work rules)
├── 📄 util.py                 # Central topology map and matrix registry (`NODE_REGISTRY`)
│
├── 📁 templates/              # Presentation layer asset directory
│   └── 📄 index.html          # Frontend telemetry dashboard (jQuery/Socket.IO)
│
└── 📁 node_logs/              # Isolated runtime I/O logging sub-directory
```

1. **Launch Orchestrator:** Boot the complete network matrix from a single terminal prompt:
   ```bash
   python run_network.py
   ```
2. **Access Web Telemetry UI:** Direct your desktop web browser interface to: `http://127.0.0.1:8080`
3. **Transaction Serialization (Queue Transfer):** Submits a transaction array (`[Sender, Receiver, Amount]`) over the WebSocket channel, appending state variables without introducing page lifecycle reloads.
4. **Synchronous Queue Block Processing:** Sequentially flushes the transaction queue, executing low-level TCP RPC lookups between the coordinator and target edge nodes to compute balances.
5. **Distributed Global State Capture (Audit):** Triggers the **Chandy-Lamport validation sequence**, propagating marker packets across the system to record a consistent ledger state and evaluate block hash references to mathematically verify the structural integrity of the blockchain.
