User logging for MVA2

Overview

- Per-user logs are stored under the Flask instance folder under `instance/users/<safe_email>/logs/`.
- Files are created per conceptual task/component, with the naming convention `<email_prefix>_<component>.log` (e.g. `alice_upload.log`).
- Each log entry is a single line, HTML is stripped and entries are truncated to `LOG_MAX_ENTRY_LENGTH`.
- Small unicode icons are prefixed to messages to make scanning easier (see `app/utils/logging_utils.py`).

Configuration

The following configuration options are available in `config.py` (or via environment variables):

- `LOG_VERBOSE_FUNCTIONS` (bool): When True, the `@log_function` decorator logs function entry and exit. Default: False.
- `LOG_MAX_ENTRY_LENGTH` (int): Maximum characters allowed per log entry. Default: 2000.
- `LOG_ROTATE_BYTES` (int): Maximum size in bytes before rotating a per-user log file. Default: 10 * 1024 * 1024 (10MB).
- `LOG_ROTATE_BACKUP_COUNT` (int): Number of rotated backup files to keep. Default: 5.

How it works

- The `UserLogger` in `app/utils/logging_utils.py` creates a `RotatingFileHandler` for each user/component pair.
- Handlers are cached per-process and closed during `teardown_appcontext` to avoid Windows file-locking issues.
- Use the provided decorators:
  - `@log_function(log_type='main')` — logs ENTER/EXIT for functions (respects `LOG_VERBOSE_FUNCTIONS`).
  - `@log_data_transform(operation, log_type='data_transform')` — logs input/output shapes for data transforms.
  - `@log_user_action(action)` — logs UI actions.
- Helper functions like `log_upload_event`, `log_analysis_event`, `log_api_request`, and others write structured single-line entries.

Frontend ingestion

- The app exposes a POST endpoint `/api/v1/logs/ingest` that accepts JSON payloads of the form:
  ```json
  { "level": "INFO", "component": "upload", "message": "User clicked start", "extra": { ... } }
  ```
- The server will write these entries to the appropriate per-user/component log file (or `anonymous` if no user is present).

Operational notes

- Keep `LOG_VERBOSE_FUNCTIONS=False` in production unless you need a trace of every function — the IO overhead is high.
- RotatingFileHandler prevents unbounded log growth; tune `LOG_ROTATE_BYTES` and `LOG_ROTATE_BACKUP_COUNT` for your storage.
- For bulk debugging, consider copying a user's logs out of the instance folder and opening in an editor that understands the single-line format.

Troubleshooting

- If you see duplicated entries, it may be because multiple handlers were attached; `UserLogger` removes previous handlers when creating a named logger.
- On Windows, ensure the app calls `user_logger.close_all_handlers()` on teardown (this is wired in `app/__init__.py`).

Contact

- For more help, check `app/utils/logging_utils.py` and search for functions starting with `log_` to find callers.
