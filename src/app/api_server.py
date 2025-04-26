from flask_jwt_extended import get_jwt_identity
from app.db_manager import DBManager

# RBAC stub
from functools import wraps
from flask import abort, request

USER_ROLES = {'admin': ['config:read', 'config:write'], 'user': ['config:read']}

def require_permission(perm):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # stub: get role from header
            role = request.headers.get('X-User-Role', 'user')
            if perm not in USER_ROLES.get(role, []):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# apply to config endpoints
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from redis import Redis
redis_client = Redis()
from flask import Flask, jsonify, request, abort
from pydantic import ValidationError
from config_manager import config_manager
from logging_config import logger
from flask_jwt_extended import JWTManager, create_access_token, jwt_require
from flask_smorest import Api, Blueprint

from flask_caching import Cache
from flask_graphql import GraphQLView
import graphene
d
from pydantic import ValidationError
from flask_cors import CORS
from pydantic import ValidationError
from flask_limiter import Limiter
from pydantic import ValidationError
from flask_limiter.util import get_remote_address
from pydantic import ValidationError
from flask_wtf.csrf import CSRFProtect
from pydantic import ValidationError
from pydantic import BaseModel, ValidationError
from werkzeug.security import check_password_hash
import datetime
import os
import json

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
FlaskInstrumentor().instrument_app(app)
app.config["RATELIMIT_DEFAULT"] = "100/hour"

api = Api(app)

# Swagger UI Configuration
app.config["API_TITLE"] = "EngineProject API"
app.config["API_VERSION"] = "1.6.0"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"



app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', config_manager.get('jwt_secret_key', 'default-secret'))
API_KEY = os.environ.get("API_KEY", config_manager.get("api_key", "default-api-key"))
jwt = JWTManager(app)
allowed_origins = config_manager.get_list('cors.allowed_origins', [])
CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
limiter = Limiter(get_remote_address, app=app)
csrf = CSRFProtect(app)

# Load user credentials from env var or config (expects dict of username:hashed_password)
users = {}
users_env = os.environ.get('API_USERS_JSON')
if users_env:
    try:
        users = json.loads(users_env)
    except Exception as e:
        logger.error("Invalid API_USERS_JSON: %s", e)
else:
    users = config_manager.get('auth.users', {})

def require_api_key(view_function):
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-KEY') != API_KEY:
            abort(401)
        return view_function(*args, **kwargs)
    decorated_function.__name__ = view_function.__name__
    return decorated_function

class LoginModel(BaseModel):
    username: str
    password: str

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        payload = LoginModel(**request.json)
    except ValidationError as ve:
        return jsonify({ 'error': ve.errors() }), 422
        return jsonify({"error": ve.errors()}), 400
    username = payload.username
    password = payload.password
    if username in users and check_password_hash(users[username], password):
        access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(hours=1))
        return jsonify(access_token=access_token)
    return abort(401)

class ConfigModel(BaseModel):
    key: str
    value: str

class ConfigUpdateModel(BaseModel):
    updates: list[ConfigModel]

@app.route('/api/config', methods=['GET'])
@limiter.limit("10 per minute")
@jwt_required()
@require_api_key
@require_permission('config:read')
def get_config():
    return jsonify(config_manager.config)

@app.route('/api/config', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
@require_api_key
@csrf.exempt
@require_permission('config:write')
def update_config():
    user = get_jwt_identity()
    db = DBManager()
    try:
        new_config = ConfigUpdateModel(**request.json)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    for item in new_config.updates:
        config_manager.config[item.key] = item.value
    with open(config_manager.config_file, 'w') as f:
        json.dump(config_manager.config, f)
    logger.info("Configurazione aggiornata via API: %s", config_manager.config)
    return jsonify(config_manager.config)

@app.route('/api/backup', methods=['POST'])
@jwt_required()
@require_api_key
@limiter.limit("5 per minute")
@csrf.exempt
def trigger_backup():
    from backup_manager import BackupManager
    bm = BackupManager(db_path=config_manager.get("db_path"), backup_interval=3600, backup_folder="backups")
    bm.start()
    return jsonify({"status": "Backup in esecuzione"}), 200

if __name__ == '__main__':
    csrf.init_app(app)
    app.run(host="0.0.0.0", port=config_manager.get("api_port", 5000))

### Swagger UI ###
blp = Blueprint('api', 'api', url_prefix='/api', description='EngineProject API')
# Register your endpoints here...
api.register_blueprint(blp)

@app.route('/api/audit/<int:record_id>', methods=['GET'])
def get_audit(record_id):
    from app.db_manager import DBManager, Audit
    session = DBManager().Session()
    entries = session.query(Audit).filter(Audit.record_id==record_id).all()
    return jsonify([{'action':e.action,'user':e.user,'old_value':e.old_value,'new_value':e.new_value,'timestamp':e.timestamp.isoformat()} for e in entries]), 200


@app.route('/swagger.json')
def swagger_json():
    return jsonify(api.spec.to_dict()), 200



@app.route('/health', methods=['GET'])
def health():
    from app.db_manager import DBManager
    try:
        DBManager().health_check()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 500

# JWT Key Rotation Stub
def rotate_jwt_key():
    # TODO: load new key from config or secrets and update JWTManager
    pass

# Schedule rotation (placeholder)
# rotate_jwt_key()

def is_token_revoked(jwt_payload):
    jti = jwt_payload['jti']
    return redis_client.sismember('revoked_tokens', jti)

# Configure JWTManager with revocation check
jwt = JWTManager(app)
jwt.token_in_blocklist_loader(is_token_revoked)

@blp.route('/logout')
class Logout(MethodView):
    @blp.doc(summary='Revoke access token')
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        redis_client.sadd('revoked_tokens', jti)
        return jsonify(msg='Token revoked'), 200


from apscheduler.schedulers.background import BackgroundScheduler

def rotate_jwt_key_job():
    # TODO: implement key rotation from secure store
    pass

# schedule key rotation daily
scheduler = BackgroundScheduler()
scheduler.add_job(rotate_jwt_key_job, 'interval', days=1)
scheduler.start()

import time
from flask import Response

@app.route('/events')
def events():
    def stream():
        while True:
            time.sleep(5)
            yield 'data: reload\n\n'
    return Response(stream(), mimetype='text/event-stream')

# JWT Key Rotation: watch config file
class KeyFileHandler(FileSystemEventHandler):
    def __init__(self, path, jwt_manager):
        self.path = path
        self.jwt_manager = jwt_manager
    def on_modified(self, event):
        if event.src_path == self.path:
            with open(self.path) as f:
                key = yaml.safe_load(f).get('jwt_key')
            self.jwt_manager._set_key(key)

# start observer
key_path = os.getenv('JWT_KEY_PATH', 'config/jwt_key.yaml')
observer = Observer()
observer.schedule(KeyFileHandler(key_path, jwt), path=os.path.dirname(key_path), recursive=False)
observer.start()


class Query(graphene.ObjectType):
    version = graphene.String()
    def resolve_version(self, info):
        from app import __version__
        return __version__

schema = graphene.Schema(query=Query)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

from flask import render_template

@app.route('/metrics/ui')
def metrics_ui():
    return render_template('metrics_ui.html')
@app.route('/api/audit/full/<int:record_id>')
    # Pagination query parameters
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    entries = session.query(Audit).filter(Audit.record_id==record_id).limit(limit).offset(offset).all()
def get_audit_full(record_id):
    from app.db_manager import DBManager, Audit
    session = DBManager().Session()
    entries = session.query(Audit).filter(Audit.record_id==record_id).all()
    return jsonify([{'old_json':e.old_json,'new_json':e.new_json} for e in entries]),200