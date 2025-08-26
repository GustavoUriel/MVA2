from flask_restx import Namespace, Resource, fields
from flask import request, current_app
from flask_login import login_required, current_user
from app.utils.logging_utils import user_logger
from app.utils.logging_utils import log_function

logs_ns = Namespace('logs', description='Frontend and client log ingestion')

log_entry = logs_ns.model('LogEntry', {
    'level': fields.String(required=True),
    'message': fields.String(required=True),
    'component': fields.String,
    'extra': fields.Raw
})


@logs_ns.route('/ingest')
class LogIngest(Resource):
  """Accept log entries from the frontend JavaScript and write them to user logs."""

  @logs_ns.expect(log_entry)
  @log_function('api')
  def post(self):
    data = request.get_json() or {}
    level = data.get('level', 'INFO').upper()
    message = data.get('message', '')
    component = data.get('component', 'frontend')
    extra = data.get('extra')

    # Use user-specific logger if available, else anonymous
    try:
      logger = user_logger.get_logger(component)
    except Exception:
      logger = user_logger.get_logger(component, email=None)

    # Attach user info if present
    user_info = None
    if current_user and getattr(current_user, 'is_authenticated', False):
      user_info = f"user={current_user.email}"

    msg = message
    if extra:
      msg = f"{msg} | extra={extra}"
    if user_info:
      msg = f"{msg} | {user_info}"

    if level == 'DEBUG':
      logger.debug(msg)
    elif level == 'WARNING' or level == 'WARN':
      logger.warning(msg)
    elif level == 'ERROR':
      logger.error(msg)
    elif level == 'CRITICAL':
      logger.critical(msg)
    else:
      logger.info(msg)

    return {'status': 'ok'}
