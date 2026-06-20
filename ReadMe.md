# Centralized Blockchain Network with Lamport's Distributed Mutual Exclusion

A high-fidelity academic platform simulating a distributed network accessing a centralized, non-replicated blockchain ledger. The framework models state synchronization, automated transaction serialization, linear ledger auditability, and distributed concurrency control. 

Crucially, the architecture utilizes **Lamport's Distributed Mutual Exclusion Algorithm** with a totally-ordered logical clock to ensure only one client modifies or queries the shared ledger at any given moment.

## Video Demonstration

[![Watch the Simulation](https://img.youtube.com/vi/K6w52aim0ig/maxresdefault.jpg)](https://youtu.be/K6w52aim0ig)

*Click the image above to watch a walk-through of the distributed synchronization execution space and telemetry dashboard.*

---

## Core Consensus & Distributed Mutual Exclusion

To safely append transactions and prevent race conditions on the untrusted server, clients must obtain exclusive access using **Lamport's Distributed Mutex Algorithm**. 

### Totally-Ordered Logical Clocks
* Each client maintains a local Lamport logical clock.
* Tie-breaking uses a totally-ordered tuple: `⟨Lamportclock, Processid⟩`.

### Three-Phase Synchronization Protocol
1. **The Request Phase:** A client increments its clock, logs its own timestamped request in its local queue, and broadcasts a `REQUEST` packet to all peer clients.
2. **The Reply Phase:** Peer clients insert the incoming request into their sorted local queues and immediately return a timestamped `REPLY` packet.
3. **The Release Phase:** After completing its critical section task, the client pops the request from its queue and broadcasts a `RELEASE` packet, prompting peers to update their queues.

### Critical Section Execution Criteria
A client process entry to the critical section (the blockchain master) occurs if and only if:
* Its own request sits at the **absolute top** of its local sorted request queue.
* It has successfully received a timestamped `REPLY` from **all** other active clients in the registry.

---

## Architectural Topology and Communication Protocol

The system enforces a strict separation of concerns across three micro-architectural tiers to handle asynchronous user events and synchronous distributed locking:

### 1. Presentation & Gateway Layer (`app.py` ➔ Port 8080)
* Hosts a non-blocking HTTP and WebSocket daemon managed by the `Flask-SocketIO` wrapper.
* Serves the event-driven HTML5 telemetry dashboard interface.
* Intercepts asynchronous browser events and serializes them before forwarding payloads to the underlying client nodes.

### 2. Coordination & Master Control Layer (`blockchain_server.py` ➔ Port 5000)
* Functions as the untrusted, centralized "blockchain master" ledger listener using raw TCP stream sockets.
* Contains a single transaction per block (`<S, R, amt>`) and builds blocks with strict linear cryptographic chaining (`SHA-256`).
* **Balance Queries:** Traverses the entire chain on-demand via \(O(N)\) linear traversal to compute balances without modifying state.
* **Transfer Spooling:** Accepts verified block proposals from the client holding the mutex, appending them directly to the chain.

### 3. Distributed Compute Nodes (`client_node.py` ➔ Dynamic Registry Ports)
* Models autonomous network participants starting with an initial ledger balance of **\$10**.
* Manage a local sorted request queue and handle the peer-to-peer `REQUEST`, `REPLY`, and `RELEASE` network message layer.
* Enforces a mandatory **3-second artificial network transmission delay** on all outbound messages to clearly demonstrate and debug concurrent race conditions.

---

## Matrix-Driven Process Lifecycle Management

The execution space relies on a generalized, cross-platform controller script (`run_network.py`) that abstracts operating system discrepancies between native Windows (Win32) environments and Linux/WSL environments.

### Topology Mapping via `NODE_REGISTRY`
The network layout avoids hardcoded configurations by dynamically bootstrapping itself from the central matrix inside `util.py`:

```python
# Sample Configuration inside util.py
NODE_REGISTRY = {
    'server': server_addr,       # Master Blockchain Server Endpoint Binding
    '1': (default_ip, 7001),     # Distributed Client Node 1
    '2': (default_ip, 7002),     # Distributed Client Node 2
    '3': (default_ip, 7003),     # Distributed Client Node 3
}
```

The orchestration engine (`run_network.py`) processes this environment schema automatically:
* **Dynamic Key Discovery:** Loops through all active keys inside `NODE_REGISTRY`, dynamically skipping the `'server'` definition to isolate and spawn edge compute nodes.
* **I/O Redirection & Isolation:** Spawns independent background processes using `subprocess.Popen`. It redirects each client node's standard output (`stdout`) and standard error (`stderr`) streams into isolated `.log` files cached in the `/node_logs/` sub-directory.
* **Deterministic Socket Reclamation:** Catches SIGINT (`Ctrl+C`) and gracefully terminates each background subprocess PID sequentially across platforms, ensuring zero ghost processes remain to lock system network sockets.

---

## System Inventory & Verification Workflow

```text
📁 (root)/
│
├── 📄 run_network.py          # Cross-platform multi-process orchestration module
├── 📄 blockchain_server.py    # Master centralized ledger daemon (Untrusted Master)
├── 📄 app.py                  # Asynchronous HTTP/WebSocket middleware gateway
├── 📄 client_node.py          # Edge client node executing Lamport Mutex logic
├── 📄 blockchain.py           # Cryptographic hashing engine (SHA-256 block rules)
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
3. **Mutex Acquisition Request:** Requesting a balance or transfer transaction causes a client to broadcast `REQUEST` packets to its peers, logging state updates with a 3-second artificial transmission delay.
4. **Synchronous Ledger Execution:** Once the client verifies it holds the distributed lock (top of its local queue + all replies received), it securely queries the blockchain master or appends a cryptographically signed transaction block.
5. **Mutex Release:** The client broadcasts a `RELEASE` packet to clear the distributed lock state, updating all peer queues so the next sequential process can proceed.
