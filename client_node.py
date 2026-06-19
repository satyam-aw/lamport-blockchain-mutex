import argparse
import socket
from pickle import loads
from client import Client
from util import max_tcp_connections

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an individual Lamport Mutex Client process.")
    parser.add_argument('--id', type=str, required=True, help="Unique identification matching registry matrix keys.")
    args_cli = parser.parse_args()

    # Instantiate the client (pulls predefined address or provisions a sequential one automatically)
    client_object = Client(id=args_cli.id)
    ip, port = client_object.client_addr
    
    # Establish raw TCP socket listener server loop
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(max_tcp_connections)
    print(f"Client {client_object.id} operational node listening actively on {ip}:{port}")
    
    while True:
        client, address = server.accept()
        message = client.recv(1024)
        if not message:
            continue
            
        args = loads(message)

        if args['sender'] == "server_request":
            client_object.receive_request_from_server(args['transaction'])
        elif args['sender'] == "server_reply":
            client_object.receive_reply_from_server(args)
        else:
            if args['operation'] == 'request':
                client_object.send_reply_to_client(args)
            elif args['operation'] == 'reply':
                client_object.receive_reply_from_client(args)
            elif args['operation'] == 'release':
                client_object.receive_release_form_client(args)
