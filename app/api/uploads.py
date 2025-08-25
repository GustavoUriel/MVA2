"""
Uploads API for analyzing and importing CSV/Excel files.

Implements requirements from prompts.txt:
- Drag & drop + browse upload support via /uploads/analyze
- Excel sheet analysis that detects data even when first row is not headers
- Date columns Start_Date/End_Date/Start_DateEng/End_DateEng get medication name prefix
- Duplicate column names are reported for user selection
- Ask user confirmation per sheet before import via /uploads/import
"""

from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import csrf
import os
import pandas as pd
from typing import Dict, Any, List
from config import BRACKEN_TIME_POINTS, Config
from ..utils.logging_utils import log_function, log_upload_event, log_data_transform, user_logger
import difflib


uploads_ns = Namespace('uploads', description='File upload and import')


analyzed_sheet = uploads_ns.model('AnalyzedSheet', {
    'sheet_name': fields.String,
    'has_data': fields.Boolean,
    'header_mode': fields.String(description="first_row or skip_first_row"),
    'columns': fields.List(fields.String),
    'duplicates': fields.Raw(description='{ name: [indices] } duplicate groups'),
    'proposed_renames': fields.Raw(description='{ old: new } renames for date prefixes'),
    'detected_type': fields.String(description='patients | taxonomy | bracken | unknown')
})


analyze_response = uploads_ns.model('AnalyzeResponse', {
    'file_name': fields.String,
    'file_type': fields.String,
    'sheets': fields.List(fields.Nested(analyzed_sheet))
})


def _user_upload_folder() -> str:
  """Return the current user's upload folder path, creating it if needed."""
  if not current_user.is_authenticated:
    raise ValueError("User not authenticated")

  safe_email = current_user.email.replace('@', '_').replace('.', '_')
  base = os.path.join(current_app.instance_path, 'users', safe_email, 'uploads')

  current_app.logger.info(f"Creating upload folder: {base}")
  current_app.logger.info(f"Instance path: {current_app.instance_path}")
  current_app.logger.info(f"User email: {current_user.email}")
  current_app.logger.info(f"Safe email: {safe_email}")

  try:
    os.makedirs(base, exist_ok=True)
    current_app.logger.info(f"Upload folder created/verified: {base}")
  except Exception as e:
    current_app.logger.exception(f"Error creating upload folder: {e}")
    raise

  return base


def _has_meaningful_data(df: pd.DataFrame) -> bool:
  """Determine if a DataFrame contains data beyond empty/NaN values."""
  if df is None or df.size == 0:
    return False
  # Consider non-empty if at least 1 non-null value exists outside a potential header row
  non_null = df.notna().sum().sum()
  return non_null > 0


@log_data_transform("Excel file analysis", 'upload')
def _analyze_excel(file_path: str) -> List[Dict[str, Any]]:
  """Analyze all sheets in an Excel file and return metadata for UI decisions."""
  log_upload_event("Starting Excel analysis", filepath=file_path)
  xls = pd.ExcelFile(file_path)
  results: List[Dict[str, Any]] = []

  for sheet in xls.sheet_names:
    log_upload_event("Analyzing Excel sheet", sheet_name=sheet, filepath=file_path)
    # Try normal header in first row
    try:
      df_first = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
    except Exception:
      df_first = pd.DataFrame()

    # Try removing the first row (header=None, then drop first row and set next as header if possible)
    try:
      tmp = pd.read_excel(file_path, sheet_name=sheet,
                          engine='openpyxl', header=None)
      df_skip = tmp.iloc[1:].reset_index(drop=True)
      # Promote first row to header if looks like header (all strings or mix reasonable)
      if not df_skip.empty:
        df_skip.columns = df_skip.iloc[0]
        df_skip = df_skip[1:].reset_index(drop=True)
    except Exception:
      df_skip = pd.DataFrame()

    # Choose the mode with more meaningful columns/data
    candidates = []
    if _has_meaningful_data(df_first):
      candidates.append(('first_row', df_first))
    if _has_meaningful_data(df_skip):
      candidates.append(('skip_first_row', df_skip))

    header_mode = 'first_row'
    df_use = df_first if not candidates else max(
        candidates, key=lambda c: c[1].notna().sum().sum()
    )[1]
    if candidates:
      header_mode = max(candidates, key=lambda c: c[1].notna().sum().sum())[0]

    has_data = _has_meaningful_data(df_use)
    columns = [str(c) for c in df_use.columns] if has_data else []

    # Proposed renames for medication date columns based on previous column name
    rename_map: Dict[str, str] = {}
    date_markers = {"Start_Date", "End_Date", "Start_DateEng", "End_DateEng"}
    for idx, col in enumerate(columns):
      if col in date_markers and idx > 0:
        prev_col = columns[idx - 1]
        rename_map[col] = f"{prev_col}_{col}"

    # Duplicate detection
    duplicates: Dict[str, List[int]] = {}
    name_to_indices: Dict[str, List[int]] = {}
    for i, name in enumerate(columns):
      name_to_indices.setdefault(name, []).append(i)
    for name, idxs in name_to_indices.items():
      if len(idxs) > 1:
        duplicates[name] = idxs

    detected_type = _detect_sheet_type(columns)

    results.append({
        'sheet_name': sheet,
        'has_data': bool(has_data),
        'header_mode': header_mode,
        'columns': columns,
        'duplicates': duplicates,
        'proposed_renames': rename_map,
        'detected_type': detected_type
    })

  return results


def _detect_sheet_type(columns: List[str]) -> str:
  """Detect the type of data in the sheet based on column names."""
  cols = {c.lower() for c in columns}
  
  # Define patient data identifiers
  patients_identifiers = {'patient_id', 'age', 'sex', 'race', 'diagnosis_date', 'stage', 'survival_months'}
  patient_columns = ['patient_id', 'age', 'sex', 'race', 'diagnosis_date', 'stage', 'survival_months', 
                    'survival_status', 'igg', 'iga', 'biclonal', 'lightchain', 'igh_rearrangement']
  
  # Define taxonomy data identifiers  
  taxonomy_identifiers = {'taxon_id', 'abundance', 'taxonomy', 'species', 'genus', 'family'}
  taxonomy_columns = ['taxon_id', 'abundance', 'taxonomy', 'species', 'genus', 'family', 'order', 'class', 'phylum']
  
  if patients_identifiers.intersection(cols):
    # Try to map columns to standard names using exact match, then fuzzy match
    mapped = 0
    for col in columns:
      if col.lower() in [c.lower() for c in patient_columns]:
        mapped += 1
      else:
        # Fuzzy match: find the closest standard name with a reasonable cutoff
        match = difflib.get_close_matches(col, patient_columns, n=1, cutoff=0.8)
        if match:
          mapped += 1
    # Heuristic: if most columns match or fuzzy-match, treat as patients table
    if mapped >= max(2, len(columns) // 2):
      return 'patients'
      
  if taxonomy_identifiers.intersection(cols):
    # Check for taxonomy data patterns
    mapped = 0
    for col in columns:
      if col.lower() in [c.lower() for c in taxonomy_columns]:
        mapped += 1
      else:
        match = difflib.get_close_matches(col, taxonomy_columns, n=1, cutoff=0.8)
        if match:
          mapped += 1
    if mapped >= max(2, len(columns) // 2):
      return 'taxonomy'
      
  # Heuristic for bracken: columns ending with configured suffixes
  suffixes = [cfg['suffix'] for cfg in BRACKEN_TIME_POINTS.values()]
  if any(any(col.endswith(suf) for suf in suffixes) for col in columns):
    return 'bracken'
    
  return 'unknown'


@log_data_transform("CSV file analysis", 'upload')
def _analyze_csv(file_path: str) -> List[Dict[str, Any]]:
  """Analyze CSV file and return metadata for UI decisions."""
  log_upload_event("Starting CSV analysis", filepath=file_path)
  # Treat CSV as single-sheet equivalent
  try:
    df_first = pd.read_csv(file_path)
  except Exception:
    df_first = pd.DataFrame()
  try:
    tmp = pd.read_csv(file_path, header=None)
    df_skip = tmp.iloc[1:].reset_index(drop=True)
    if not df_skip.empty:
      df_skip.columns = df_skip.iloc[0]
      df_skip = df_skip[1:].reset_index(drop=True)
  except Exception:
    df_skip = pd.DataFrame()

  candidates = []
  if _has_meaningful_data(df_first):
    candidates.append(('first_row', df_first))
  if _has_meaningful_data(df_skip):
    candidates.append(('skip_first_row', df_skip))

  header_mode = 'first_row'
  df_use = df_first if not candidates else max(
      candidates, key=lambda c: c[1].notna().sum().sum()
  )[1]
  if candidates:
    header_mode = max(candidates, key=lambda c: c[1].notna().sum().sum())[0]

  has_data = _has_meaningful_data(df_use)
  columns = [str(c) for c in df_use.columns] if has_data else []

  rename_map: Dict[str, str] = {}
  date_markers = {"Start_Date", "End_Date", "Start_DateEng", "End_DateEng"}
  for idx, col in enumerate(columns):
    if col in date_markers and idx > 0:
      prev_col = columns[idx - 1]
      rename_map[col] = f"{prev_col}_{col}"

  duplicates: Dict[str, List[int]] = {}
  name_to_indices: Dict[str, List[int]] = {}
  for i, name in enumerate(columns):
    name_to_indices.setdefault(name, []).append(i)
  for name, idxs in name_to_indices.items():
    if len(idxs) > 1:
      duplicates[name] = idxs

  detected_type = _detect_sheet_type(columns)

  return [{
      'sheet_name': 'CSV',
      'has_data': bool(has_data),
      'header_mode': header_mode,
      'columns': columns,
      'duplicates': duplicates,
      'proposed_renames': rename_map,
      'detected_type': detected_type
  }]


@uploads_ns.route('/analyze')
class UploadAnalyze(Resource):
  """Analyze uploaded file (multipart/form-data) and return sheet metadata."""

  method_decorators = [login_required]  # type: ignore

  @uploads_ns.response(200, 'Success', analyze_response)
  @log_function('upload')
  def post(self):
    log_upload_event("File upload analyze started", user=current_user.email, ip=request.remote_addr)
    
    file = request.files.get('file')
    if not file or file.filename == '':
      log_upload_event("Upload failed - no file provided", user=current_user.email)
      return {'message': 'No file provided'}, 400

    filename = secure_filename(file.filename)
    file_size = len(file.read())
    file.seek(0)  # Reset file pointer
    
    log_upload_event("File received for analysis", 
                    filename=filename, size_bytes=file_size, user=current_user.email)

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    allowed_extensions = Config.ALLOWED_EXTENSIONS
    if ext not in allowed_extensions:
      log_upload_event("Upload failed - invalid file type", 
                      filename=filename, extension=ext, user=current_user.email)
      return {'message': f'File type not allowed: .{ext}'}, 400

    try:
      upload_dir = _user_upload_folder()
      file_path = os.path.join(upload_dir, filename)
      file.save(file_path)
      log_upload_event("File saved successfully", 
                      filename=filename, path=file_path, user=current_user.email)
    except Exception as e:
      log_upload_event("File save failed", 
                      filename=filename, error=str(e), user=current_user.email)
      user_logger.log_error('upload', e, f'File save: {filename}')
      return {'message': f'Error saving file: {e}'}, 500

    try:
      log_upload_event("Starting file analysis", 
                      filename=filename, file_type=ext, user=current_user.email)
      
      if ext in {'xlsx', 'xls'}:
        sheets = _analyze_excel(file_path)
      else:
        sheets = _analyze_csv(file_path)
        
      log_upload_event("File analysis completed", 
                      filename=filename, sheets_found=len(sheets), user=current_user.email)
                      
    except Exception as e:
      log_upload_event("File analysis failed", 
                      filename=filename, error=str(e), user=current_user.email)
      user_logger.log_error('upload', e, f'File analysis: {filename}')
      return {'message': f'Analyze failed: {e}'}, 500

    return {
        'file_name': filename,
        'file_type': ext,
        'sheets': sheets
    }


import_request = uploads_ns.model('ImportRequest', {
    'file_name': fields.String(required=True),
    'file_type': fields.String(required=True),
    'selections': fields.Raw(required=True, description='Per-sheet selections: header_mode, renames, duplicate_keep, confirmed, detected_type')
})


@uploads_ns.route('/import')
class UploadImport(Resource):
  """Import a previously analyzed file according to user selections."""

  method_decorators = [login_required, csrf.exempt]  # type: ignore

  @uploads_ns.expect(import_request)
  @log_function('upload')
  def post(self):
    log_upload_event("File import started", user=current_user.email, ip=request.remote_addr)
    
    payload = request.get_json(silent=True) or {}
    file_name = payload.get('file_name')
    file_type = payload.get('file_type')
    selections: Dict[str, Any] = payload.get('selections') or {}

    log_upload_event("Import request details", 
                    filename=file_name, file_type=file_type, 
                    sheets_selected=len(selections), user=current_user.email)

    if not file_name or not file_type:
      log_upload_event("Import failed - missing parameters", user=current_user.email)
      return {'message': 'file_name and file_type are required'}, 400

    src_path = os.path.join(_user_upload_folder(), secure_filename(file_name))
    if not os.path.exists(src_path):
      log_upload_event("Import failed - file not found", 
                      filename=file_name, path=src_path, user=current_user.email)
      return {'message': 'File not found on server'}, 400

    imported = []
    try:
      if file_type in {'xlsx', 'xls'}:
        xls = pd.ExcelFile(src_path)
        for sheet, sel in selections.items():
          if not sel.get('confirmed'):
            continue
          header_mode = sel.get('header_mode', 'first_row')
          if header_mode == 'skip_first_row':
            df = pd.read_excel(src_path, sheet_name=sheet,
                               engine='openpyxl', header=None)
            df = df.iloc[1:].reset_index(drop=True)
            if not df.empty:
              df.columns = df.iloc[0]
              df = df[1:].reset_index(drop=True)
          else:
            df = pd.read_excel(src_path, sheet_name=sheet, engine='openpyxl')

          # Apply renames (e.g., medication date prefixes)
          renames: Dict[str, str] = sel.get('renames') or {}
          if renames:
            df = df.rename(columns=renames)

          # Resolve duplicates by index to keep
          duplicate_keep: Dict[str, int] = sel.get('duplicate_keep') or {}
          for name, keep_idx in duplicate_keep.items():
            # Keep the chosen column, drop others
            cols_same = [c for c in df.columns if str(c) == name]
            for i, col in enumerate(cols_same):
              if i != keep_idx and col in df.columns:
                df = df.drop(columns=[col])

          # Save a normalized CSV per sheet into user folder
          out_name = f"import_{os.path.splitext(file_name)[0]}_{sheet}.csv"
          out_path = os.path.join(_user_upload_folder(), out_name)
          
          log_upload_event("Processing sheet data", 
                          sheet_name=sheet, input_shape=df.shape, 
                          user=current_user.email)
          
          df.to_csv(out_path, index=False)
          
          log_upload_event("Sheet data saved", 
                          sheet_name=sheet, output_path=out_name, 
                          rows=int(df.shape[0]), cols=int(df.shape[1]),
                          user=current_user.email)
          
          imported.append({'sheet': sheet, 'rows': int(
              df.shape[0]), 'cols': int(df.shape[1]), 'path': out_path})

      else:
        # CSV single-sheet equivalent
        sel = selections.get('CSV') or {}
        if sel.get('confirmed'):
          if sel.get('header_mode') == 'skip_first_row':
            df = pd.read_csv(src_path, header=None)
            df = df.iloc[1:].reset_index(drop=True)
            if not df.empty:
              df.columns = df.iloc[0]
              df = df[1:].reset_index(drop=True)
          else:
            df = pd.read_csv(src_path)

          renames: Dict[str, str] = sel.get('renames') or {}
          if renames:
            df = df.rename(columns=renames)

          duplicate_keep: Dict[str, int] = sel.get('duplicate_keep') or {}
          for name, keep_idx in duplicate_keep.items():
            cols_same = [c for c in df.columns if str(c) == name]
            for i, col in enumerate(cols_same):
              if i != keep_idx and col in df.columns:
                df = df.drop(columns=[col])

          out_name = f"import_{os.path.splitext(file_name)[0]}.csv"
          out_path = os.path.join(_user_upload_folder(), out_name)
          df.to_csv(out_path, index=False)
          imported.append({'sheet': 'CSV', 'rows': int(
              df.shape[0]), 'cols': int(df.shape[1]), 'path': out_path})

    except Exception as e:
      log_upload_event("Import processing failed", 
                      filename=file_name, error=str(e), user=current_user.email)
      user_logger.log_error('upload', e, f'File import: {file_name}')
      return {'message': f'Import failed: {e}'}, 500

    log_upload_event("Import completed successfully", 
                    filename=file_name, imported_count=len(imported), 
                    total_rows=sum(item.get('rows', 0) for item in imported),
                    user=current_user.email)

    return {'message': 'Import completed', 'imported': imported}
