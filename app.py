from flask import Flask, render_template, session, copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock
from util import *


async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socket_ = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
queue = []

@app.route('/')
def index():
    return render_template('index.html')

@socket_.on('my_event')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']})

@socket_.on('queue_transfer')
def queue_transfer(message):
    session['receive_count'] = session.get('receive_count', 0) + 1

    emit('my_response', {'data': f"Enqueued transfer of ${message['data'][2]} from {message['data'][0]} to {message['data'][1]}", 'count': session['receive_count']})
    transaction = {
        'type': 'send_money',
        'from': message['data'][0],
        'to': message['data'][1],
        'amount': message['data'][2]
    }
    data = {
        'sender': 'server_request',
        'transaction': transaction
    }
    queue.append(data)
    
@socket_.on('execute_all_transfer')
def execute_all_transfer():
    session['receive_count'] = session.get('receive_count', 0) + 1
    if not queue:
        emit('my_response', {'data': f"No transfers to enqueue! Please enqueue a transfer request first.", 'count': session['receive_count']})
        return
    while queue:

        data = queue.pop(0)
        if data['transaction']['type']=='send_money':
            sndr, rcvr, amt = data['transaction']['from'],data['transaction']['to'],data['transaction']['amount']
            emit('my_response', {'data': f"Now processing transfer of ${amt} from {sndr} to {rcvr}", 'count': session['receive_count']})       
        else:
            emit('my_response', {'data': f"Now processing balance inquiry for {data['transaction']['from']}", 'count': session['receive_count']})       
        send_data(data['transaction']['from'], data)

@socket_.on('check_valid')
def check_valid():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': "Validating the blockchain......", 'count': session['receive_count']}, broadcast=True)
    transaction = {
        'type': 'validate',
    }
    data = {
        'sender': 'server_request',
        'transaction': transaction
    }
    send_data('server', data)

@socket_.on('balance_inquiry')
def balance_inquiry(message):
    print("\nbalance inquiry ")
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': f"Enqueued balance inquiry for {message['data']}", 'count': session['receive_count']}, broadcast=True)

    transaction = {
        'type': 'balance',
        'from': message['data'],
    }
    data = {
        'sender': 'server_request',
        'transaction': transaction
    }
    queue.append(data)

@socket_.on('send_money_result')
def send_money_result(message):
    result, sndr, rcvr, amt = message['result'], message['data'][0],message['data'][1],message['data'][2]
    emit('my_response', {'data': f"Transfer of {amt} from {sndr} to {rcvr} was a {result}", 'count': '?'}, broadcast=True)
    print(result)
    if result=='pass':
        emit('append_chain', {'sndr':sndr,'rcvr':rcvr, 'amt':amt}, broadcast=True)

@socket_.on('balance_inquiry_result')
def balance_inquiry_result(message):  
    sndr, amt = message['data'], message['amt']
    emit('my_response', {'data': f"Current balance of {sndr} is ${amt}", 'count': '?'}, broadcast=True)
    emit('balance_print', {'sndr': sndr, 'amt':amt }, broadcast=True)

@socket_.on('check_valid_result')
def check_valid_result(message):
    msg = message['data']
    emit('my_response', {'data': msg, 'count': '?'}, broadcast=True)


@socket_.on('disconnect_request')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()        

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Disconnected!', 'count': session['receive_count']}, callback=can_disconnect)


if __name__ == '__main__':
    
    socket_.run(app, debug=False, port=8080)