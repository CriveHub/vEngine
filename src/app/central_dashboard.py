from flask import Flask, jsonify, request, send_from_directory
from logging_config import logger
from VPLC.engine_manager import engine_manager
import asyncio
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, verify_jwt_in_request, get_jwt_identity
from flask_socketio import SocketIO, emit, disconnect
from markupsafe import escape
from config_manager import config_manager
import ssl
from flask_wtf.csrf import CSRFProtect, csrf_exempt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['JWT_SECRET_KEY'] = config_manager.get('jwt_secret_key', 'default-secret')

CORS(app, resources={r"/*": {"origins": "*"}})

csrf = CSRFProtect(app)

jwt = JWTManager(app)
# Restrictive CORS for SocketIO
cors_origins = config_manager.get_list('cors.allowed_origins', ['https://your.domain'])

context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.load_cert_chain('cert.pem', 'key.pem')

socketio = SocketIO(app, cors_allowed_origins=cors_origins, ssl_context=context)

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.after_request
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
def set_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self'; "
        "connect-src 'self' wss:; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    return response

@app.route('/engines', methods=['GET'])
@jwt_required()
def list_engines():
    raw = engine_manager.list_engines()
    safe = [escape(str(item)) for item in raw]
    return jsonify(safe)

@app.route('/engines', methods=['POST'])
@csrf_exempt
@jwt_required()
def add_engine():
    data = request.json
    engine_id = escape(data.get("engine_id", ""))
    logic_filepath = escape(data.get("logic_filepath", "dynamic_logic_classes.py"))
    cycle_time = data.get("cycle_time", 0.005)
    db_path = escape(data.get("db_path", "states_test.db"))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine_manager.add_engine(engine_id, logic_filepath, cycle_time, db_path))
    return jsonify({"status": "Engine aggiunto", "engine_id": engine_id})

@app.route('/engines/<engine_id>', methods=['DELETE'])
@jwt_required()
def delete_engine(engine_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine_manager.remove_engine(engine_id))
    return jsonify({"status": "Engine rimosso", "engine_id": engine_id})

@app.route('/engines/<engine_id>/pause', methods=['POST'])
@csrf_exempt
@jwt_required()
def pause_engine(engine_id):
    safe_engine_id = escape(engine_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine_manager.pause_engine(safe_engine_id))
    return jsonify({"status": "Engine in pausa", "engine_id": safe_engine_id})

@app.route('/engines/<engine_id>/resume', methods=['POST'])
@csrf_exempt
@jwt_required()
def resume_engine(engine_id):
    safe_engine_id = escape(engine_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine_manager.resume_engine(safe_engine_id))
    return jsonify({"status": "Engine ripreso", "engine_id": safe_engine_id})

@socketio.on('connect')
def ws_connect():
    try:
        verify_jwt_in_request()
    except Exception as e:
        logger.warning(f"WebSocket connection rejected due to JWT verification failure: {e}")
        disconnect()
        return False  # reject connection
    emit('status', {'msg': 'Connected'}, broadcast=False)

# Note: WebSocket TLS support to be integrated later with Flask-SocketIO.

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8000, ssl_context=context)

@socketio.on('status')
def ws_status():
    # send basic engine status
    status = {'version': __version__}
    socketio.emit('status_response', status)
