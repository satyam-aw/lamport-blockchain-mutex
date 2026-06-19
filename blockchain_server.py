import socket
from pickle import dumps, loads
import socketio

# Academic project module imports
from blockchain import Blockchain
from util import server_addr, max_tcp_connections, initialBalance, send_data

# Initialize core engines
blockchain = Blockchain()
sio_frontEnd = socketio.Client()

# ==========================================
# 1. INTERNAL BLOCKCHAIN LEDGER METHODS
# ==========================================

def mine_block_internal(sndr, rcvr, amt):
    """Executes the Proof-of-Work algorithm and appends a verified transaction block."""
    data = {'sndr': sndr, "rcvr": rcvr, "amt": amt}
    previous_block = blockchain.print_previous_block()
    previous_proof = previous_block['proof']
    
    # Execute cryptographic local mining
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    
    return blockchain.create_block(proof, previous_hash, data)

def validate_chain_internal():
    """Evaluates blockchain structural integrity."""
    is_valid = blockchain.chain_valid(blockchain.chain)
    if is_valid:
        return {'data': 'The Blockchain is valid.'}
    return {'data': 'The Blockchain is not valid.'}

def getBalance(user="me"):
    """Calculates liquid client balances via O(N) linear traversal."""
    chain = blockchain.chain
    current_balance = initialBalance

    for block in chain:
        try:
            block_data = block['data']
            if block_data['sndr'] == user:
                current_balance -= int(block_data['amt'])
            if block_data['rcvr'] == user:
                current_balance += int(block_data['amt'])
        except (KeyError, ValueError):
            continue
            
    return current_balance

def makeTransaction(sndr, rcvr, amt):
    """Enforces state safety boundaries before mining transaction events."""
    balance = getBalance(sndr)
    if balance < int(amt):
        return "fail"
    
    mine_block_internal(sndr, rcvr, amt)
    return "pass"


# ==========================================
# 2. WEBSOCKET VISUALIZATION PUSH LAYER
# ==========================================

def inform_front_end(event, message):
    """Dispatches asynchronous real-time events straight up to the app.py UI engine."""
    if not sio_frontEnd.connected:
        try:
            # Connects directly to the frontend server running on port 8080
            sio_frontEnd.connect("http://127.0.0.1:8080")
        except Exception:
            print("[VISUALIZATION WRAPPER] UI Frontend Server (app.py) offline or unreachable.")
            return
            
    sio_frontEnd.emit(event, message)


# ==========================================
# 3. MASTER TCP SOCKET SERVER RUNNER
# ==========================================

if __name__ == "__main__":
    # Initialize low-level raw TCP server socket properties on configuration ports
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(server_addr) # server_addr must resolve to ('127.0.0.1', 5000) inside util.py
    server.listen(max_tcp_connections)
    print(f"[SYSTEM ENGINE] Master Ledger TCP Engine listening actively on {server_addr[0]}:{server_addr[1]}")
    
    while True:
        client_sock, address = server.accept()
        print(f"Inbound Network Connection Established - {address[0]}:{address[1]}")
        
        try:
            message = client_sock.recv(1024)
            if not message:
                continue
                
            args = loads(message)
            transaction = args['transaction']
            client_id = str(args['from'])
            
            # --- RPC ROUTING ROUTINES ---
            if transaction['type'] == 'send_money':
                result = makeTransaction(transaction['from'], transaction['to'], transaction['amount'])
                reply_payload = {'sender': 'server_reply', 'result': result}
                
                # Send confirmation status back to the specific edge client node
                send_data(client_id, reply_payload)
                
                # Instantly mirror the transaction result visually to the browser
                inform_front_end('send_money_result', {
                    'data': [transaction['from'], transaction['to'], transaction['amount']],
                    'result': result
                })
                
            elif transaction['type'] == 'balance':
                amt = str(getBalance(client_id))
                reply_payload = {'sender': 'server_reply', 'result': amt}
                
                # Send balance data back to the specific edge client node
                send_data(client_id, reply_payload)
                
                # Instantly mirror the balance inquiry visually to the browser
                inform_front_end('balance_inquiry_result', {
                    'data': client_id, 
                    'amt': amt
                })
            
            elif transaction['type'] == 'validate':            
                # Push blockchain verification results to the browser dashboard
                inform_front_end('check_valid_result', validate_chain_internal())
                
        except Exception as e:
            print(f"[CRITICAL ERROR] Transaction RPC Pipeline Failure: {e}")
        finally:
            client_sock.close()
