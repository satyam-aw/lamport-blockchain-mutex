import threading
import time
from util import NODE_REGISTRY, get_or_create_node_address, get_all_peer_ids, send_data
import random

class Client:
    def __init__(self, id):
        print('Initializing client ', id)
        self.time = 0
        self.queue = []
        self.id = str(id)
        self.replies = 0
        self.lock = threading.Lock()
        
        # Pull or auto-generate the network mapping from the central utility layer
        self.client_addr = get_or_create_node_address(self.id)

    def receive_request_from_server(self, transaction):
        print('Received request from server. Transaction: ', str(transaction))
        with self.lock:
            self.time += 1
            args = {
                'time': self.time,
                'sender': self.id,
                'transaction': transaction
            }
            self.add_to_queue(args)
        self.send_requests_to_clients(args)

    def receive_reply_from_client(self, args):
        print('Received reply from ', args['sender'])
        total_peers_required = len(get_all_peer_ids(self.id))
        
        with self.lock:
            self.replies += 1
            can_execute = (self.replies >= total_peers_required)
            
        if can_execute:
            self.execute()
    
    def receive_release_form_client(self, args):
        print('Release received from .............', args['sender'])
        released_sender = str(args['sender'])
        
        with self.lock:
            # Drop the specific transaction tied to the releasing sender node
            self.queue = [req for req in self.queue if req[1] != released_sender]
            print(f'Queue state post-release: {list([x[0:2] for x in self.queue])}')
            
        self.execute()
    
    def thread_function_execute(self):
        with self.lock:
            print('Head of execution queue: ', list([x[0:2] for x in self.queue]))
        
        # Generates a random float between 0.1 and 1.0 seconds (100ms to 1000ms)
        time.sleep(random.uniform(0.1, 1.0))
        total_peers_required = len(get_all_peer_ids(self.id))
        data_to_send = None
        
        with self.lock:
            # Condition check: All peer nodes replied AND your request sits at the queue head
            if self.replies >= total_peers_required and self.queue and self.queue[0][1] == self.id:
                print('Executing transfer request')
                self.replies -= total_peers_required
                data = self.queue.pop(0)
                data_to_send = {
                    'transaction': data[2],
                    'from': self.id
                }
                
        if data_to_send:
            send_data('server', data_to_send)
            
    def execute(self):
        x = threading.Thread(target=self.thread_function_execute, args=())
        x.start()

    def thread_function_send_requests(self, args):
        # Generates a random float between 0.1 and 1.0 seconds (100ms to 1000ms)
        time.sleep(random.uniform(0.1, 1.0))

        print('Sending requests to clients....')
        for target_node in get_all_peer_ids(self.id):
            data = {
                'operation': 'request',
                'sender': self.id,
                'time': args['time'],
                'transaction': args['transaction']
            }
            send_data(target_node, data)

    def send_requests_to_clients(self, args):
        x = threading.Thread(target=self.thread_function_send_requests, args=(args,))
        x.start()
                
    def add_to_queue(self, args):
        self.queue.append([args['time'], str(args['sender']), args['transaction']])
        # Order priorities cleanly: Sort by timestamp scalar first, break ties using node ID values
        self.queue.sort(key=lambda x: (x[0], int(x[1])))
        print('Adding new request', list([x[0:2] for x in self.queue]))

    def send_reply_to_client(self, args):
        print('Sending reply to client', args['sender'])
        with self.lock:
            self.time = max(self.time, args['time']) + 1
            self.add_to_queue(args)
            current_time = self.time
        
        data = {
            'operation': 'reply',
            'sender': self.id,
            'time': current_time
        }
        send_data(str(args['sender']), data)

    def receive_reply_from_server(self, args):
        print('Finished execution. Reply from server: ', args['result'])
        with self.lock:
            self.time += 1
            current_time = self.time
            
        for target_node in get_all_peer_ids(self.id):
            data = {
                'operation': 'release',
                'sender': self.id,
                'time': current_time
            }
            send_data(target_node, data)
