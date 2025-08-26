from app.utils.logging_utils import log_function
from flask_restx import Namespace, Resource
from flask import send_file, abort, current_app, request
from flask_login import login_required, current_user
import os

admin_ns = Namespace('admin_logs', description='Admin access to user logs')


def _ensure_admin():
  # Allow access if user is admin role or has an explicit permission (flexible policy)
  if not (current_user and getattr(current_user, 'is_authenticated', False)):
    abort(403, 'Admin privileges required')

  try:
    if getattr(current_user, 'role', '') == 'admin':
      return
    # Prefer has_permission if available
    if hasattr(current_user, 'has_permission') and current_user.has_permission('manage_users'):
      return
  except Exception:
    pass

  abort(403, 'Admin privileges required')


@admin_ns.route('/users/<string:email>/logs/<string:component>/download')
class AdminDownloadLog(Resource):
  @login_required
  @log_function('admin')
  def get(self, email, component):
    _ensure_admin()
    safe_email = email.replace('@', '_').replace('.', '_')
    user_logs = os.path.join(current_app.instance_path,
                             'users', safe_email, 'logs')
    log_filename = f"{email.split('@')[0]}_{component}.log"
    path = os.path.join(user_logs, log_filename)
    if not os.path.exists(path):
      abort(404, 'Log file not found')
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))


@admin_ns.route('/users/<string:email>/logs/<string:component>/tail')
class AdminTailLog(Resource):
  @login_required
  @log_function('admin')
  def get(self, email, component):
    _ensure_admin()
    lines = int(request.args.get('lines', 200))
    safe_email = email.replace('@', '_').replace('.', '_')
    user_logs = os.path.join(current_app.instance_path,
                             'users', safe_email, 'logs')
    log_filename = f"{email.split('@')[0]}_{component}.log"
    path = os.path.join(user_logs, log_filename)
    if not os.path.exists(path):
      abort(404, 'Log file not found')

    # Read last N lines efficiently
    def tail(path, n):
      with open(path, 'rb') as f:
        avg_line_length = 200
        to_read = n * avg_line_length
        try:
          f.seek(-to_read, os.SEEK_END)
        except Exception:
          f.seek(0)
        data = f.read().decode('utf-8', errors='replace')
        lines_data = data.splitlines()
        return '\n'.join(lines_data[-n:])

    content = tail(path, lines)
    return {'email': email, 'component': component, 'lines': lines, 'tail': content}


@admin_ns.route('/users/<string:email>/logs/<string:component>/stream')
class AdminStreamLog(Resource):
  @login_required
  @log_function('admin')
  def get(self, email, component):
    _ensure_admin()
    # Optional query params
    follow = request.args.get('follow', 'true').lower() != 'false'
    timeout = int(request.args.get('timeout', 300))  # seconds to keep streaming
    safe_email = email.replace('@', '_').replace('.', '_')
    user_logs = os.path.join(current_app.instance_path,
                             'users', safe_email, 'logs')
    log_filename = f"{email.split('@')[0]}_{component}.log"
    path = os.path.join(user_logs, log_filename)
    if not os.path.exists(path):
      abort(404, 'Log file not found')

    def generate():
      try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
          # Start at end of file
          f.seek(0, os.SEEK_END)
          import time
          start = time.time()
          while True:
            line = f.readline()
            if line:
              yield f"data: {line.strip()}\n\n"
            else:
              if not follow:
                break
              if time.time() - start > timeout:
                break
              time.sleep(0.5)
      except GeneratorExit:
        return
      except Exception:
        return

    from flask import Response
    return Response(generate(), mimetype='text/event-stream')
