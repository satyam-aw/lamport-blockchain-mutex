import socket
from pickle import dumps

# Global Configuration Parameters
initialBalance = 10
max_tcp_connections = 15
default_ip = "127.0.0.1"
server_addr = (default_ip, 1234)

# Central Network Registry Matrix
NODE_REGISTRY = {
    'server': server_addr,
    '1': (default_ip, 9711),
    '2': (default_ip, 9712),
    '3': (default_ip, 9713),
    '4': (default_ip, 9714), 
    '5': (default_ip, 9715),
}


def get_or_create_node_address(node_id):
    """
    Looks up a node address in the registry. If it is a new node ID, 
    it dynamically allocates the next available sequential port.
    """
    node_str = str(node_id)
    
    # Return directly if already configured
    if node_str in NODE_REGISTRY:
        return NODE_REGISTRY[node_str]
        
    # Dynamically allocate the next available network slot
    allocated_ports = [addr[1] for addr in NODE_REGISTRY.values()]
    next_port = max(allocated_ports) + 1 if allocated_ports else 8001
    
    # Save the new assignment into global memory
    NODE_REGISTRY[node_str] = (default_ip, next_port)
    print(f"[DYNAMIC REGISTER] Auto-assigned Client {node_str} to port {next_port}")
    return NODE_REGISTRY[node_str]

def send_data(destination, data):
    """Dispatches a network payload safely using the centralized registry."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    if isinstance(destination, tuple):
        client_addr = destination
    else:
        client_addr = get_or_create_node_address(destination)

    try:
        client.connect(client_addr)
        operation = dumps(data)
        client.sendall(operation)
    except ConnectionRefusedError:
        print(f"[ERROR] Target node '{destination}' at {client_addr} is offline.")
    finally:
        client.close()

def get_all_peer_ids(current_node_id):
    """Returns all valid participant peer IDs currently stored in the registry."""
    return [k for k in NODE_REGISTRY.keys() if k != 'server' and k != str(current_node_id)]
