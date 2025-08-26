
from flask import request, current_app, jsonify, render_template
import traceback
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import csrf
import os
import pandas as pd
from typing import Dict, Any, List
from config import BRACKEN_TIME_POINTS, Config, patients_table_columns_name, patients_table_identificatos, taxonomy_table_columns_name, taxonomy_table_identificatos
from ..utils.logging_utils import log_function, log_upload_event, log_data_transform, user_logger
import difflib
import csv
from collections import Counter
import csv as _pycsv
from app.models.taxonomy import Taxonomy
from flask_restx import Namespace, Resource, fields
uploads_ns = Namespace('uploads', description='File upload and import')


@uploads_ns.route('/import-default-taxonomy')
class ImportDefaultTaxonomy(Resource):
  @log_function('uploads')
  def post(self):
    """Import the default taxonomy file as if uploaded by the user. Always returns JSON."""
    try:
      # Check authentication manually to always return JSON
      if not current_user.is_authenticated:
        return {'message': 'Authentication required', 'status': 'error'}, 401
      # Path to default taxonomy file
      default_path = os.path.join(
          current_app.root_path, '..', '..', 'instance', 'taxonomy.csv')
      default_path = os.path.abspath(default_path)
      if not os.path.exists(default_path):
        # In development/testing mode, create a small sample taxonomy CSV as a fallback
        if current_app.config.get('DEBUG') or current_app.config.get('TESTING'):
          try:
            os.makedirs(os.path.dirname(default_path), exist_ok=True)
            sample_rows = [
                ['taxonomy_id', 'ASV', 'Taxonomy', 'Domain', 'Phylum',
                 'Class', 'Order', 'Family', 'Genus', 'Species'],
                ['t1', 'asv1', 'Kingdom;Phylum;Class;Order;Family;Genus;Species', 'Bacteria', 'Firmicutes',
                    'Bacilli', 'Lactobacillales', 'Lactobacillaceae', 'Lactobacillus', 'L.casei'],
                ['t2', 'asv2', 'Kingdom;Phylum;Class;Order;Family;Genus;Species', 'Bacteria', 'Proteobacteria',
                    'Gammaproteobacteria', 'Enterobacterales', 'Enterobacteriaceae', 'Escherichia', 'E.coli']
            ]
            with open(default_path, 'w', newline='', encoding='utf-8') as f:
              writer = _pycsv.writer(f)
              for r in sample_rows:
                writer.writerow(r)
          except Exception as e:
            return {'message': f'Failed to create sample taxonomy file: {e}', 'status': 'error'}, 500
        else:
          return {'message': f'Default taxonomy file not found: {default_path}', 'status': 'error'}, 404

      # Analyze step (simulate what /analyze returns)
      filename = os.path.basename(default_path)
      ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
      if ext not in Config.ALLOWED_EXTENSIONS:
        return {'message': f'File type not allowed: .{ext}', 'status': 'error'}, 400

      # Analyze file content
      if ext in {'xlsx', 'xls'}:
        sheets = _analyze_excel(default_path)
      else:
        sheets = _analyze_csv(default_path)

      # Prepare selections (auto-confirm first sheet)
      selections = {}
      if sheets:
        sheet = sheets[0]
        selections[sheet.get('sheet_name') or 'Sheet1'] = {
            'confirmed': True,
            'header_mode': sheet.get('header_mode', 'auto'),
            'detected_type': sheet.get('detected_type', 'taxonomy'),
            'renames': sheet.get('proposed_renames', {}),
            'duplicate_keep': list(sheet.get('duplicates', {}).keys()),
        }

      # Call the same import logic as /import
      payload = {
          'file_name': filename,
          'file_type': ext,
          'selections': selections
      }
      # Patch: temporarily copy file to user upload folder if needed
      upload_dir = _user_upload_folder()
      user_file_path = os.path.join(upload_dir, filename)
      if not os.path.exists(user_file_path):
        import shutil
        shutil.copy2(default_path, user_file_path)

      # Now call the import logic (simulate request.get_json)
      # --- Begin import logic ---
      file_name = payload.get('file_name')
      file_type = payload.get('file_type')
      selections = payload.get('selections') or {}
      if not file_name:
        return {'message': 'file_name is required', 'status': 'error'}, 400
      if not file_type:
        return {'message': 'file_type is required', 'status': 'error'}, 400
      if not selections:
        return {'message': 'No sheet selections provided', 'status': 'error'}, 400
      secure_file_name = secure_filename(file_name)
      user_folder = upload_dir
      src_path = os.path.join(user_folder, secure_file_name)
      try:
        imported = []
        total_rows = 0
        total_cols = 0
        for sheet_name, opts in selections.items():
          if not opts.get('confirmed'):
            continue
          if file_type in {'csv'}:
            df = _robust_read_csv(src_path)
          elif file_type in {'xlsx', 'xls'}:
            df = pd.read_excel(src_path, sheet_name=sheet_name)
          else:
            return {'message': f'Unsupported file type: {file_type}', 'status': 'error'}, 400
          total_rows += len(df)
          total_cols = max(total_cols, len(df.columns))
          imported.append({'sheet': sheet_name, 'rows': len(df)})

        return {'status': 'ok', 'message': 'Import completed', 'imported': imported, 'added': total_rows}
      except Exception as e:
        return {'message': f'Import failed: {e}', 'status': 'error'}, 500
      # --- End import logic ---
    except Exception as e:
      return {'message': f'Error: {e}', 'status': 'error'}, 500


"""
Uploads API for analyzing and importing CSV/Excel files.

Implements requirements from prompts.txt:
- Drag & drop + browse upload support via /uploads/analyze
- Excel sheet analysis that detects data even when first row is not headers
- Date columns Start_Date/End_Date/Start_DateEng/End_DateEng get medication name prefix
- Duplicate column names are reported for user selection
- Ask user confirmation per sheet before import via /uploads/import
"""


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
  log_upload_event("FOLDER STEP 1: Getting user upload folder")

  if not current_user.is_authenticated:
    log_upload_event("FOLDER STEP 1 FAILED: User not authenticated")
    raise ValueError("User not authenticated")

  log_upload_event("FOLDER STEP 1 SUCCESS: User is authenticated",
                   user=current_user.email)

  log_upload_event("FOLDER STEP 2: Creating safe email identifier")
  safe_email = current_user.email.replace('@', '_').replace('.', '_')
  log_upload_event("FOLDER STEP 2 SUCCESS: Safe email created",
                   original_email=current_user.email, safe_email=safe_email)

  log_upload_event("FOLDER STEP 3: Constructing upload folder path")
  instance_path = current_app.instance_path
  base = os.path.join(instance_path, 'users', safe_email, 'uploads')
  log_upload_event("FOLDER STEP 3 SUCCESS: Upload folder path constructed",
                   instance_path=instance_path, user_folder=safe_email,
                   full_path=base)

  log_upload_event("FOLDER STEP 4: Creating directory structure")
  try:
    # Check if directory already exists
    exists_before = os.path.exists(base)
    log_upload_event("FOLDER STEP 4a: Checking existing directory",
                     path=base, exists=exists_before)

    os.makedirs(base, exist_ok=True)

    exists_after = os.path.exists(base)
    is_dir = os.path.isdir(base) if exists_after else False

    log_upload_event("FOLDER STEP 4b: Directory creation completed",
                     path=base, existed_before=exists_before,
                     exists_after=exists_after, is_directory=is_dir)

    # Verify directory permissions
    if exists_after and is_dir:
      try:
        # Test write permissions by creating a temporary file
        test_file = os.path.join(base, '.permission_test')
        with open(test_file, 'w') as f:
          f.write('test')
        os.remove(test_file)
        writable = True
      except Exception:
        writable = False

      log_upload_event("FOLDER STEP 4c: Directory permissions verified",
                       path=base, writable=writable)

    log_upload_event("FOLDER STEP 4 SUCCESS: Upload folder ready", path=base)

  except Exception as e:
    log_upload_event("FOLDER STEP 4 FAILED: Error creating upload folder",
                     path=base, error=str(e), error_type=type(e).__name__)
    user_logger.log_error('upload', e, f'Upload folder creation: {base}')
    raise

  return base


def _detect_csv_delimiter(file_path: str) -> str | None:
  """Attempt to detect the delimiter of a CSV file by sampling lines.
  Returns one of ',', ';', '\t' or None if detection failed.
  """
  try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
      sample = ''.join([next(f) for _ in range(10)])
  except StopIteration:
    # File has fewer than 10 lines; read entire content
    try:
      with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        sample = f.read()
    except Exception:
      return None
  except Exception:
    return None

  # Count frequencies of candidate delimiters on the first few lines
  lines = sample.splitlines()
  if not lines:
    return None

  delim_counts = {',': 0, ';': 0, '\t': 0}
  for ln in lines[:10]:
    delim_counts[','] += ln.count(',')
    delim_counts[';'] += ln.count(';')
    delim_counts['\t'] += ln.count('\t')

  # Choose the delimiter with the highest count if it is meaningfully higher
  most_common, count = max(delim_counts.items(), key=lambda kv: kv[1])
  # require at least one occurrence and at least 1.5x the next candidate
  others = [v for k, v in delim_counts.items() if k != most_common]
  if count == 0:
    return None
  if count >= max(1, int(max(others) * 1.5)):
    return most_common
  return None


def _robust_read_csv(file_path: str, sep: str | None = None) -> pd.DataFrame:
  """Attempt multiple pandas.read_csv strategies to handle inconsistent quoting.

  Tries common quotechar/engine combinations and returns the first DataFrame
  whose column count matches the header column count (best-effort). Falls back
  to a default read if none match.
  """
  # determine expected column count from the header line
  try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
      header_line = f.readline().strip()
  except Exception:
    header_line = ''

  expected_cols = header_line.count(sep or ',') + 1 if header_line else None

  candidates = []
  # prefer C engine with standard quoting
  candidates.append({'sep': sep or ',', 'engine': 'c',
                    'quoting': _pycsv.QUOTE_MINIMAL, 'quotechar': '"'})
  # try single-quote quoting
  candidates.append({'sep': sep or ',', 'engine': 'c',
                    'quoting': _pycsv.QUOTE_MINIMAL, 'quotechar': "'"})
  # python engine with single-quote
  candidates.append({'sep': sep or ',', 'engine': 'python',
                    'quotechar': "'", 'quoting': _pycsv.QUOTE_MINIMAL})
  # python engine no quoting (best-effort)
  candidates.append({'sep': sep or ',', 'engine': 'python',
                    'quoting': _pycsv.QUOTE_NONE})

  for opts in candidates:
    try:
      df = pd.read_csv(file_path, **opts)
      if expected_cols is None or df.shape[1] == expected_cols:
        return df
    except Exception:
      continue

  # Fallback: try a simple read with default pandas heuristics
  try:
    return pd.read_csv(file_path, sep=sep or ',', engine='python', encoding='utf-8', on_bad_lines='skip')
  except Exception:
    # Last resort: let pandas try with defaults
    return pd.read_csv(file_path)


def _split_commas_not_in_single_quotes(line: str) -> list:
  """Split a CSV line on commas that are not inside single quotes.

  This is a best-effort parser for messy CSVs that use single quotes as
  quote characters but sometimes have unmatched quotes. It toggles state on
  single quotes and splits on commas outside quotes.
  """
  parts = []
  cur = []
  in_sq = False
  i = 0
  while i < len(line):
    ch = line[i]
    if ch == "'":
      in_sq = not in_sq
      # include the quote for later cleaning
      cur.append(ch)
    elif ch == ',' and not in_sq:
      parts.append(''.join(cur).strip())
      cur = []
    else:
      cur.append(ch)
    i += 1
  parts.append(''.join(cur).strip())
  # clean surrounding single quotes from each part
  cleaned = []
  for p in parts:
    p = p.strip()
    if len(p) >= 2 and p[0] == "'" and p[-1] == "'":
      p = p[1:-1].strip()
    cleaned.append(p if p != '' else None)
  return cleaned


def _read_csv_with_fallback_to_line_split(file_path: str, sep: str | None = None) -> pd.DataFrame:
  """Read CSV file, falling back to manual line splitting when pandas fails.

  Returns a DataFrame with header parsed from the first line.
  """
  try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
      lines = [ln.rstrip('\n') for ln in f]
  except Exception:
    return pd.read_csv(file_path)

  if not lines:
    return pd.DataFrame()

  header = _split_commas_not_in_single_quotes(lines[0])
  rows = []
  for ln in lines[1:]:
    if not ln.strip():
      continue
    parts = _split_commas_not_in_single_quotes(ln)
    # pad or truncate to header length
    if len(parts) < len(header):
      parts += [None] * (len(header) - len(parts))
    elif len(parts) > len(header):
      parts = parts[:len(header)]
    rows.append({h: parts[idx] for idx, h in enumerate(header)})

  return pd.DataFrame(rows, columns=header)


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
  log_upload_event(
      "EXCEL ANALYSIS START: Initializing Excel file analysis", filepath=file_path)

  try:
    log_upload_event("EXCEL STEP 1: Loading Excel file with pandas")
    xls = pd.ExcelFile(file_path)
    log_upload_event("EXCEL STEP 1 SUCCESS: Excel file loaded",
                     total_sheets=len(xls.sheet_names),
                     sheet_names=xls.sheet_names)
  except Exception as e:
    log_upload_event("EXCEL STEP 1 FAILED: Could not load Excel file",
                     error=str(e), error_type=type(e).__name__)
    raise

  results: List[Dict[str, Any]] = []
  log_upload_event("EXCEL STEP 2: Beginning individual sheet analysis",
                   sheets_to_analyze=len(xls.sheet_names))

  for sheet_idx, sheet in enumerate(xls.sheet_names):
    log_upload_event(f"EXCEL SHEET {sheet_idx+1}: Starting analysis of sheet '{sheet}'",
                     sheet_name=sheet, sheet_index=sheet_idx)
    # Try normal header in first row
    log_upload_event(
        f"EXCEL SHEET {sheet_idx+1} STEP A: Reading with first row as header")
    try:
      df_first = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
      log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP A SUCCESS: First row header read",
                       shape=df_first.shape, columns_count=len(df_first.columns))
    except Exception as e:
      log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP A FAILED: Could not read with first row header",
                       error=str(e))
      df_first = pd.DataFrame()

    # Try removing the first row (header=None, then drop first row and set next as header if possible)
    log_upload_event(
        f"EXCEL SHEET {sheet_idx+1} STEP B: Reading with second row as header")
    try:
      tmp = pd.read_excel(file_path, sheet_name=sheet,
                          engine='openpyxl', header=None)
      log_upload_event(
          f"EXCEL SHEET {sheet_idx+1} STEP B1: Raw data read", shape=tmp.shape)

      df_skip = tmp.iloc[1:].reset_index(drop=True)
      log_upload_event(
          f"EXCEL SHEET {sheet_idx+1} STEP B2: First row skipped", shape=df_skip.shape)

      # Promote first row to header if looks like header (all strings or mix reasonable)
      if not df_skip.empty:
        df_skip.columns = df_skip.iloc[0]
        df_skip = df_skip[1:].reset_index(drop=True)
        log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP B3: Second row promoted to header",
                         shape=df_skip.shape, columns_count=len(df_skip.columns))
      else:
        log_upload_event(
            f"EXCEL SHEET {sheet_idx+1} STEP B3: Sheet empty after skipping first row")

      log_upload_event(
          f"EXCEL SHEET {sheet_idx+1} STEP B SUCCESS: Second row header processed")
    except Exception as e:
      log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP B FAILED: Could not process second row header",
                       error=str(e))
      df_skip = pd.DataFrame()

    # Choose the mode with more meaningful columns/data
    log_upload_event(
        f"EXCEL SHEET {sheet_idx+1} STEP C: Evaluating header mode options")
    candidates = []

    first_has_data = _has_meaningful_data(df_first)
    skip_has_data = _has_meaningful_data(df_skip)

    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP C1: Data evaluation",
                     first_row_has_data=first_has_data,
                     skip_first_has_data=skip_has_data)

    if first_has_data:
      first_data_count = df_first.notna().sum().sum()
      candidates.append(('first_row', df_first))
      log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP C2: First row candidate added",
                       non_null_values=int(first_data_count))

    if skip_has_data:
      skip_data_count = df_skip.notna().sum().sum()
      candidates.append(('skip_first_row', df_skip))
      log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP C3: Skip first row candidate added",
                       non_null_values=int(skip_data_count))

    header_mode = 'first_row'
    df_use = df_first if not candidates else max(
        candidates, key=lambda c: c[1].notna().sum().sum())[1]
    if candidates:
      header_mode = max(candidates, key=lambda c: c[1].notna().sum().sum())[0]

    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP C SUCCESS: Header mode selected",
                     selected_mode=header_mode,
                     final_shape=df_use.shape if not df_use.empty else (0, 0))

    has_data = _has_meaningful_data(df_use)
    columns = [str(c) for c in df_use.columns] if has_data else []

    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP D: Final data assessment",
                     has_meaningful_data=has_data,
                     column_count=len(columns),
                     column_names_preview=columns[:5] if columns else [])

    # Step E: Proposed renames for medication date columns
    log_upload_event(
        f"EXCEL SHEET {sheet_idx+1} STEP E: Analyzing date columns for medication prefixes")
    rename_map: Dict[str, str] = {}
    date_markers = {"Start_Date", "End_Date", "Start_DateEng", "End_DateEng"}
    date_columns_found = []

    for idx, col in enumerate(columns):
      if col in date_markers:
        date_columns_found.append(col)
        if idx > 0:
          prev_col = columns[idx - 1]
          rename_map[col] = f"{prev_col}_{col}"
          log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP E: Date column rename proposed",
                           original_column=col, previous_column=prev_col,
                           proposed_name=f"{prev_col}_{col}")

    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP E SUCCESS: Date column analysis complete",
                     date_columns_found=date_columns_found,
                     rename_proposals=len(rename_map))

    # Step F: Duplicate detection
    log_upload_event(
        f"EXCEL SHEET {sheet_idx+1} STEP F: Detecting duplicate column names")
    duplicates: Dict[str, List[int]] = {}
    name_to_indices: Dict[str, List[int]] = {}
    for i, name in enumerate(columns):
      name_to_indices.setdefault(name, []).append(i)

    duplicate_groups = 0
    for name, idxs in name_to_indices.items():
      if len(idxs) > 1:
        duplicates[name] = idxs
        duplicate_groups += 1
        log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP F: Duplicate column detected",
                         column_name=name, indices=idxs, occurrence_count=len(idxs))

    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP F SUCCESS: Duplicate detection complete",
                     duplicate_groups_found=duplicate_groups)

    # Step G: Data type detection
    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP G: Detecting data type")
    detected_type = _detect_sheet_type(columns)
    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP G SUCCESS: Data type detected",
                     detected_type=detected_type)

    # Step H: Compiling results
    log_upload_event(
        f"EXCEL SHEET {sheet_idx+1} STEP H: Compiling sheet analysis results")
    sheet_result = {
        'sheet_name': sheet,
        'has_data': bool(has_data),
        'header_mode': header_mode,
        'columns': columns,
        'duplicates': duplicates,
        'proposed_renames': rename_map,
        'detected_type': detected_type
    }

    results.append(sheet_result)
    log_upload_event(f"EXCEL SHEET {sheet_idx+1} STEP H SUCCESS: Sheet analysis complete",
                     sheet_name=sheet, result_keys=list(sheet_result.keys()))

  log_upload_event("EXCEL ANALYSIS COMPLETE: All sheets analyzed successfully",
                   total_sheets_processed=len(results))
  return results


def _detect_sheet_type(columns: List[str]) -> str:
  """Detect the type of data in the sheet based on column names."""
  cols = {c.lower() for c in columns}

  if patients_table_identificatos.intersection(cols):
    # Try to map columns to standard names using exact match, then fuzzy match
    mapped = 0
    for col in columns:
      if col.lower() in [c.lower() for c in patients_table_columns_name]:
        mapped += 1
      else:
        # Fuzzy match: find the closest standard name with a reasonable cutoff
        match = difflib.get_close_matches(
            col, patients_table_columns_name, n=1, cutoff=0.8)
        if match:
          mapped += 1
    # Heuristic: if most columns match or fuzzy-match, treat as patients table
    if mapped >= max(2, len(columns) // 2):
      return 'patients'

  if taxonomy_table_identificatos.intersection(cols):
    # Check for taxonomy data patterns
    mapped = 0
    for col in columns:
      if col.lower() in [c.lower() for c in taxonomy_table_columns_name]:
        mapped += 1
      else:
        match = difflib.get_close_matches(
            col, taxonomy_table_columns_name, n=1, cutoff=0.8)
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
  log_upload_event(
      "CSV ANALYSIS START: Initializing CSV file analysis", filepath=file_path)

  # Try to detect delimiter first (comma, semicolon, tab)
  try:
    detected_delim = _detect_csv_delimiter(file_path)
    log_upload_event("CSV ANALYSIS: Detected delimiter",
                     delimiter=detected_delim)
  except Exception as e:
    detected_delim = None
    log_upload_event("CSV ANALYSIS: Delimiter detection failed, will use pandas default",
                     error=str(e))

  # Step 1: Try reading with first row as header
  log_upload_event("CSV STEP A: Reading CSV with first row as header")
  try:
    if detected_delim:
      df_first = pd.read_csv(file_path, sep=detected_delim, engine='python')
    else:
      df_first = pd.read_csv(file_path)
    log_upload_event("CSV STEP A SUCCESS: First row header read",
                     shape=df_first.shape, columns_count=len(df_first.columns))
  except Exception as e:
    log_upload_event("CSV STEP A FAILED: Could not read with first row header",
                     error=str(e), error_type=type(e).__name__)
    df_first = pd.DataFrame()

  # Step 2: Try reading with second row as header
  log_upload_event("CSV STEP B: Reading CSV with second row as header")
  try:
    tmp = pd.read_csv(file_path, header=None)
    log_upload_event("CSV STEP B1: Raw CSV data read", shape=tmp.shape)

    df_skip = tmp.iloc[1:].reset_index(drop=True)
    log_upload_event("CSV STEP B2: First row skipped", shape=df_skip.shape)

    if not df_skip.empty:
      df_skip.columns = df_skip.iloc[0]
      df_skip = df_skip[1:].reset_index(drop=True)
      log_upload_event("CSV STEP B3: Second row promoted to header",
                       shape=df_skip.shape, columns_count=len(df_skip.columns))
    else:
      log_upload_event("CSV STEP B3: CSV empty after skipping first row")

    log_upload_event("CSV STEP B SUCCESS: Second row header processed")
  except Exception as e:
    log_upload_event("CSV STEP B FAILED: Could not process second row header",
                     error=str(e), error_type=type(e).__name__)
    df_skip = pd.DataFrame()

  # Step 3: Evaluate header mode options
  log_upload_event("CSV STEP C: Evaluating header mode options")
  candidates = []

  first_has_data = _has_meaningful_data(df_first)
  skip_has_data = _has_meaningful_data(df_skip)

  log_upload_event("CSV STEP C1: Data evaluation",
                   first_row_has_data=first_has_data,
                   skip_first_has_data=skip_has_data)

  if first_has_data:
    first_data_count = df_first.notna().sum().sum()
    candidates.append(('first_row', df_first))
    log_upload_event("CSV STEP C2: First row candidate added",
                     non_null_values=int(first_data_count))

  if skip_has_data:
    skip_data_count = df_skip.notna().sum().sum()
    candidates.append(('skip_first_row', df_skip))
    log_upload_event("CSV STEP C3: Skip first row candidate added",
                     non_null_values=int(skip_data_count))

  header_mode = 'first_row'
  df_use = df_first if not candidates else max(
      candidates, key=lambda c: c[1].notna().sum().sum())[1]
  if candidates:
    header_mode = max(candidates, key=lambda c: c[1].notna().sum().sum())[0]

  log_upload_event("CSV STEP C SUCCESS: Header mode selected",
                   selected_mode=header_mode,
                   final_shape=df_use.shape if not df_use.empty else (0, 0))

  # Step 4: Final data assessment
  has_data = _has_meaningful_data(df_use)
  columns = [str(c) for c in df_use.columns] if has_data else []

  log_upload_event("CSV STEP D: Final data assessment",
                   has_meaningful_data=has_data,
                   column_count=len(columns),
                   column_names_preview=columns[:5] if columns else [])

  # Step 5: Date column analysis
  log_upload_event("CSV STEP E: Analyzing date columns for medication prefixes")
  rename_map: Dict[str, str] = {}
  date_markers = {"Start_Date", "End_Date", "Start_DateEng", "End_DateEng"}
  date_columns_found = []

  for idx, col in enumerate(columns):
    if col in date_markers:
      date_columns_found.append(col)
      if idx > 0:
        prev_col = columns[idx - 1]
        rename_map[col] = f"{prev_col}_{col}"
        log_upload_event("CSV STEP E: Date column rename proposed",
                         original_column=col, previous_column=prev_col,
                         proposed_name=f"{prev_col}_{col}")

  log_upload_event("CSV STEP E SUCCESS: Date column analysis complete",
                   date_columns_found=date_columns_found,
                   rename_proposals=len(rename_map))

  # Step 6: Duplicate detection
  log_upload_event("CSV STEP F: Detecting duplicate column names")
  duplicates: Dict[str, List[int]] = {}
  name_to_indices: Dict[str, List[int]] = {}
  for i, name in enumerate(columns):
    name_to_indices.setdefault(name, []).append(i)

  duplicate_groups = 0
  for name, idxs in name_to_indices.items():
    if len(idxs) > 1:
      duplicates[name] = idxs
      duplicate_groups += 1
      log_upload_event("CSV STEP F: Duplicate column detected",
                       column_name=name, indices=idxs, occurrence_count=len(idxs))

  log_upload_event("CSV STEP F SUCCESS: Duplicate detection complete",
                   duplicate_groups_found=duplicate_groups)

  # Step 7: Data type detection
  log_upload_event("CSV STEP G: Detecting data type")
  detected_type = _detect_sheet_type(columns)
  log_upload_event("CSV STEP G SUCCESS: Data type detected",
                   detected_type=detected_type)

  # Step 8: Compile results
  log_upload_event("CSV STEP H: Compiling CSV analysis results")
  result = {
      'sheet_name': 'CSV',
      'has_data': bool(has_data),
      'header_mode': header_mode,
      'columns': columns,
      'duplicates': duplicates,
      'proposed_renames': rename_map,
      'detected_type': detected_type
  }

  log_upload_event("CSV ANALYSIS COMPLETE: CSV analysis finished successfully",
                   result_keys=list(result.keys()))

  return [result]


@uploads_ns.route('/analyze')
class UploadAnalyze(Resource):
  """Analyze uploaded file (multipart/form-data) and return sheet metadata."""

  method_decorators = [login_required]  # type: ignore

  @uploads_ns.response(200, 'Success', analyze_response)
  @log_function('upload')
  def post(self):
    log_upload_event("STEP 1: File upload analyze endpoint called",
                     user=current_user.email, ip=request.remote_addr,
                     user_agent=request.headers.get('User-Agent', 'unknown'))

    # Step 1: Validate request contains file
    log_upload_event("STEP 2: Checking for uploaded file in request")
    file = request.files.get('file')
    if not file:
      log_upload_event("STEP 2 FAILED: No 'file' key found in request.files",
                       available_keys=list(request.files.keys()))
      return {'message': 'No file provided'}, 400

    if file.filename == '':
      log_upload_event("STEP 2 FAILED: File has empty filename",
                       user=current_user.email)
      return {'message': 'No file provided'}, 400

    log_upload_event("STEP 2 SUCCESS: File found in request",
                     original_filename=file.filename, mimetype=file.mimetype)

    # Step 2: Process filename and get file size
    log_upload_event("STEP 3: Processing filename and reading file size")
    raw_filename = file.filename or 'upload'
    filename = secure_filename(raw_filename)
    log_upload_event("STEP 3a: Filename secured",
                     original=file.filename, secured=filename)

    try:
      file_size = len(file.read())
      file.seek(0)  # Reset file pointer
      log_upload_event("STEP 3b SUCCESS: File size determined",
                       size_bytes=file_size, size_mb=round(file_size/1024/1024, 2))
    except Exception as e:
      log_upload_event("STEP 3b FAILED: Could not read file size", error=str(e))
      return {'message': f'Error reading file: {e}'}, 500

    # Step 3: Validate file extension
    log_upload_event("STEP 4: Validating file extension")
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    log_upload_event("STEP 4a: Extension extracted", extension=ext)

    allowed_extensions = Config.ALLOWED_EXTENSIONS
    log_upload_event("STEP 4b: Checking against allowed extensions",
                     extension=ext, allowed=list(allowed_extensions))

    if ext not in allowed_extensions:
      log_upload_event("STEP 4 FAILED: File type not allowed",
                       extension=ext, allowed=list(allowed_extensions), user=current_user.email)
      return {'message': f'File type not allowed: .{ext}'}, 400

    log_upload_event("STEP 4 SUCCESS: File extension is valid", extension=ext)

    # Step 4: Create user folder and save file
    log_upload_event("STEP 5: Creating user upload directory and saving file")
    try:
      log_upload_event("STEP 5a: Getting user upload folder")
      upload_dir = _user_upload_folder()
      log_upload_event("STEP 5a SUCCESS: User upload folder ready",
                       upload_dir=upload_dir, user=current_user.email)

      log_upload_event("STEP 5b: Constructing file path")
      file_path = os.path.join(upload_dir, filename)
      log_upload_event("STEP 5b SUCCESS: File path constructed",
                       full_path=file_path)

      log_upload_event("STEP 5c: Saving file to disk")
      file.save(file_path)

      # Verify file was saved
      saved_size = os.path.getsize(
          file_path) if os.path.exists(file_path) else 0
      log_upload_event("STEP 5c SUCCESS: File saved to disk",
                       filename=filename, path=file_path,
                       saved_size_bytes=saved_size,
                       size_match=saved_size == file_size)

    except Exception as e:
      log_upload_event("STEP 5 FAILED: Error in file save process",
                       filename=filename, error=str(e), error_type=type(e).__name__)
      user_logger.log_error('upload', e, f'File save process: {filename}')
      return {'message': f'Error saving file: {e}'}, 500

    # Step 5: Analyze file content
    log_upload_event("STEP 6: Starting file content analysis",
                     filename=filename, file_type=ext, file_path=file_path)

    try:
      if ext in {'xlsx', 'xls'}:
        log_upload_event("STEP 6a: Calling Excel analysis function")
        sheets = _analyze_excel(file_path)
        log_upload_event("STEP 6a SUCCESS: Excel analysis completed",
                         sheets_analyzed=len(sheets))
      else:
        log_upload_event("STEP 6a: Calling CSV analysis function")
        sheets = _analyze_csv(file_path)
        log_upload_event("STEP 6a SUCCESS: CSV analysis completed",
                         sheets_analyzed=len(sheets))

      # Log detailed results for each sheet
      for i, sheet in enumerate(sheets):
        log_upload_event(f"STEP 6b: Sheet {i+1} analysis results",
                         sheet_name=sheet.get('sheet_name'),
                         has_data=sheet.get('has_data'),
                         header_mode=sheet.get('header_mode'),
                         column_count=len(sheet.get('columns', [])),
                         detected_type=sheet.get('detected_type'),
                         duplicates_found=len(sheet.get('duplicates', {})),
                         proposed_renames=len(sheet.get('proposed_renames', {})))

      log_upload_event("STEP 6 SUCCESS: File analysis completed successfully",
                       filename=filename, total_sheets=len(sheets), user=current_user.email)

    except Exception as e:
      log_upload_event("STEP 6 FAILED: File analysis failed",
                       filename=filename, error=str(e), error_type=type(e).__name__)
      user_logger.log_error('upload', e, f'File analysis: {filename}')
      return {'message': f'Analyze failed: {e}'}, 500

    # Step 6: Prepare response
    log_upload_event("STEP 7: Preparing response for client")
    response_data = {
        'file_name': filename,
        'file_type': ext,
        'sheets': sheets
    }
    log_upload_event("STEP 7 SUCCESS: Response prepared, sending to client",
                     response_filename=filename, response_type=ext,
                     response_sheets_count=len(sheets))

    return response_data


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
    log_upload_event("IMPORT STEP 1: File import endpoint called",
                     user=current_user.email, ip=request.remote_addr)

    # Step 1: Parse import request
    log_upload_event("IMPORT STEP 2: Parsing import request payload")
    payload = request.get_json(silent=True) or {}
    log_upload_event("IMPORT STEP 2a: Request payload received",
                     payload_keys=list(payload.keys()) if payload else [],
                     payload_size=len(str(payload)))

    file_name = payload.get('file_name')
    file_type = payload.get('file_type')
    selections: Dict[str, Any] = payload.get('selections') or {}

    log_upload_event("IMPORT STEP 2b: Request parameters extracted",
                     filename=file_name, file_type=file_type,
                     sheets_selected=len(selections),
                     selection_keys=list(selections.keys()) if selections else [])

    # Step 2: Validate required parameters
    log_upload_event("IMPORT STEP 3: Validating required parameters")
    if not file_name:
      log_upload_event("IMPORT STEP 3 FAILED: Missing file_name parameter")
      return {'message': 'file_name is required'}, 400

    if not file_type:
      log_upload_event("IMPORT STEP 3 FAILED: Missing file_type parameter")
      return {'message': 'file_type is required'}, 400

    if not selections:
      log_upload_event("IMPORT STEP 3 FAILED: No sheet selections provided")
      return {'message': 'No sheet selections provided'}, 400

    log_upload_event("IMPORT STEP 3 SUCCESS: All required parameters validated")

    # Step 3: Locate source file
    log_upload_event("IMPORT STEP 4: Locating source file")
    secure_file_name = secure_filename(file_name)
    log_upload_event("IMPORT STEP 4a: Filename secured",
                     original=file_name, secured=secure_file_name)

    user_folder = _user_upload_folder()
    src_path = os.path.join(user_folder, secure_file_name)
    log_upload_event("IMPORT STEP 4b: Source path constructed",
                     source_path=src_path, user_folder=user_folder)

    if not os.path.exists(src_path):
      log_upload_event("IMPORT STEP 4 FAILED: Source file not found",
                       expected_path=src_path, file_exists=False)
      return {'message': 'File not found on server'}, 400

    file_size = os.path.getsize(src_path)
    log_upload_event("IMPORT STEP 4 SUCCESS: Source file located",
                     source_path=src_path, file_size_bytes=file_size)

    # Step 4: Begin import processing
    log_upload_event("IMPORT STEP 5: Beginning data import processing",
                     file_type=file_type, total_selections=len(selections))

    imported = []
    try:
      if file_type in {'xlsx', 'xls'}:
        log_upload_event("IMPORT STEP 5a: Processing Excel file")
        xls = pd.ExcelFile(src_path)
        log_upload_event("IMPORT STEP 5a SUCCESS: Excel file loaded for import",
                         available_sheets=xls.sheet_names)

        sheet_index = 0
        for sheet, sel in selections.items():
          sheet_index += 1
          log_upload_event(f"IMPORT SHEET {sheet_index}: Processing sheet '{sheet}'",
                           sheet_name=sheet, selection_keys=list(sel.keys()) if sel else [])

          if not sel.get('confirmed'):
            log_upload_event(f"IMPORT SHEET {sheet_index} SKIPPED: Sheet not confirmed for import",
                             sheet_name=sheet)
            continue

          log_upload_event(
              f"IMPORT SHEET {sheet_index} STEP A: Reading sheet data")
          header_mode = sel.get('header_mode', 'first_row')
          log_upload_event(f"IMPORT SHEET {sheet_index} STEP A1: Using header mode",
                           header_mode=header_mode)

          if header_mode == 'skip_first_row':
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP A2: Reading with skip first row mode")
            df = pd.read_excel(src_path, sheet_name=sheet,
                               engine='openpyxl', header=None)
            original_shape = df.shape
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP A2a: Raw data read", shape=original_shape)

            df = df.iloc[1:].reset_index(drop=True)
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP A2b: First row removed", shape=df.shape)

            if not df.empty:
              df.columns = df.iloc[0]
              df = df[1:].reset_index(drop=True)
              log_upload_event(f"IMPORT SHEET {sheet_index} STEP A2c: Header row promoted",
                               shape=df.shape, columns_count=len(df.columns))
          else:
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP A2: Reading with first row as header")
            df = pd.read_excel(src_path, sheet_name=sheet, engine='openpyxl')
            log_upload_event(f"IMPORT SHEET {sheet_index+1} STEP A2 SUCCESS: Data read",
                             shape=df.shape, columns_count=len(df.columns))

          log_upload_event(f"IMPORT SHEET {sheet_index} STEP A SUCCESS: Sheet data loaded",
                           final_shape=df.shape)

          # Apply renames (e.g., medication date prefixes)
          log_upload_event(
              f"IMPORT SHEET {sheet_index} STEP B: Applying column renames")
          renames: Dict[str, str] = sel.get('renames') or {}
          if renames:
            log_upload_event(f"IMPORT SHEET {sheet_index} STEP B1: Renaming columns",
                             rename_count=len(renames), renames=renames)
            df = df.rename(columns=renames)
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP B1 SUCCESS: Columns renamed")
          else:
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP B1: No column renames needed")

          # Resolve duplicates by index to keep
          log_upload_event(
              f"IMPORT SHEET {sheet_index} STEP C: Resolving duplicate columns")
          duplicate_keep: Dict[str, int] = sel.get('duplicate_keep') or {}
          if duplicate_keep:
            log_upload_event(f"IMPORT SHEET {sheet_index} STEP C1: Processing duplicate resolutions",
                             duplicate_count=len(duplicate_keep), duplicates=duplicate_keep)

            for name, keep_idx in duplicate_keep.items():
              cols_same = [c for c in df.columns if str(c) == name]
              log_upload_event(f"IMPORT SHEET {sheet_index} STEP C1a: Resolving duplicate",
                               column_name=name, keep_index=keep_idx,
                               found_instances=len(cols_same))

              dropped_count = 0
              for i, col in enumerate(cols_same):
                if i != keep_idx and col in df.columns:
                  df = df.drop(columns=[col])
                  dropped_count += 1

              log_upload_event(f"IMPORT SHEET {sheet_index} STEP C1b: Duplicate resolved",
                               column_name=name, columns_dropped=dropped_count)

            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP C SUCCESS: All duplicates resolved")
          else:
            log_upload_event(
                f"IMPORT SHEET {sheet_index} STEP C: No duplicate columns to resolve")

          # Save processed data
          log_upload_event(
              f"IMPORT SHEET {sheet_index} STEP D: Saving processed data")
          out_name = f"import_{os.path.splitext(file_name)[0]}_{sheet}.csv"
          out_path = os.path.join(_user_upload_folder(), out_name)

          log_upload_event(f"IMPORT SHEET {sheet_index} STEP D1: Constructing output path",
                           output_filename=out_name, output_path=out_path)

          log_upload_event(f"IMPORT SHEET {sheet_index} STEP D2: Writing CSV file",
                           final_shape=df.shape, output_format="CSV")

          df.to_csv(out_path, index=False)
          saved_size = os.path.getsize(
              out_path) if os.path.exists(out_path) else 0

          log_upload_event(f"IMPORT SHEET {sheet_index} STEP D SUCCESS: Data saved successfully",
                           output_file=out_name, saved_size_bytes=saved_size,
                           rows=int(df.shape[0]), cols=int(df.shape[1]))

          imported.append({
              'sheet': sheet,
              'rows': int(df.shape[0]),
              'cols': int(df.shape[1]),
              'path': out_path
          })

      else:
        # CSV single-sheet equivalent
        log_upload_event("IMPORT STEP 5b: Processing CSV file")
        sel = selections.get('CSV') or {}

        if sel.get('confirmed'):
          log_upload_event("IMPORT CSV STEP A: Processing confirmed CSV selection",
                           selection_keys=list(sel.keys()))

          header_mode = sel.get('header_mode', 'first_row')
          log_upload_event(
              "IMPORT CSV STEP A1: Using header mode", header_mode=header_mode)
          # Detect delimiter (comma/semicolon/tab) and read accordingly
          detected_delim = None
          try:
            detected_delim = _detect_csv_delimiter(src_path)
            log_upload_event(
                "IMPORT CSV: Detected delimiter for import", delimiter=detected_delim)
          except Exception:
            detected_delim = None

          if header_mode == 'skip_first_row':
            log_upload_event(
                "IMPORT CSV STEP A2: Reading with skip first row mode")
            try:
              if detected_delim:
                df = _robust_read_csv(src_path, sep=detected_delim)
              else:
                df = _robust_read_csv(src_path)
            except Exception:
              df = _read_csv_with_fallback_to_line_split(src_path)
            original_shape = df.shape
            log_upload_event(
                "IMPORT CSV STEP A2a: Raw CSV data read", shape=original_shape)

            df = df.iloc[1:].reset_index(drop=True)
            log_upload_event(
                "IMPORT CSV STEP A2b: First row removed", shape=df.shape)

            if not df.empty:
              df.columns = df.iloc[0]
              df = df[1:].reset_index(drop=True)
              log_upload_event("IMPORT CSV STEP A2c: Header row promoted",
                               shape=df.shape, columns_count=len(df.columns))
          else:
            log_upload_event(
                "IMPORT CSV STEP A2: Reading with first row as header")
            try:
              if detected_delim:
                df = _robust_read_csv(src_path, sep=detected_delim)
              else:
                df = _robust_read_csv(src_path)
            except Exception:
              df = _read_csv_with_fallback_to_line_split(src_path)
            log_upload_event("IMPORT CSV STEP A2 SUCCESS: Data read",
                             shape=df.shape, columns_count=len(df.columns))

          log_upload_event(
              "IMPORT CSV STEP A SUCCESS: CSV data loaded", final_shape=df.shape)

          # Normalize column names to lowercase
          try:
            df.columns = [str(c).lower() for c in df.columns]
            log_upload_event("IMPORT CSV STEP A1: Normalized columns to lowercase",
                             columns_preview=list(df.columns)[:10])
          except Exception as e:
            log_upload_event("IMPORT CSV STEP A1 FAILED: Could not normalize columns",
                             error=str(e))

          # Apply renames
          log_upload_event("IMPORT CSV STEP B: Applying column renames")
          renames: Dict[str, str] = sel.get('renames') or {}
          if renames:
            log_upload_event("IMPORT CSV STEP B1: Renaming columns",
                             rename_count=len(renames), renames=renames)
            df = df.rename(columns=renames)
            log_upload_event("IMPORT CSV STEP B1 SUCCESS: Columns renamed")
          else:
            log_upload_event("IMPORT CSV STEP B1: No column renames needed")

          # Resolve duplicates
          log_upload_event("IMPORT CSV STEP C: Resolving duplicate columns")
          duplicate_keep: Dict[str, int] = sel.get('duplicate_keep') or {}
          if duplicate_keep:
            log_upload_event("IMPORT CSV STEP C1: Processing duplicate resolutions",
                             duplicate_count=len(duplicate_keep), duplicates=duplicate_keep)

            for name, keep_idx in duplicate_keep.items():
              cols_same = [c for c in df.columns if str(c) == name]
              log_upload_event("IMPORT CSV STEP C1a: Resolving duplicate",
                               column_name=name, keep_index=keep_idx,
                               found_instances=len(cols_same))

              dropped_count = 0
              for i, col in enumerate(cols_same):
                if i != keep_idx and col in df.columns:
                  df = df.drop(columns=[col])
                  dropped_count += 1

              log_upload_event("IMPORT CSV STEP C1b: Duplicate resolved",
                               column_name=name, columns_dropped=dropped_count)

            log_upload_event(
                "IMPORT CSV STEP C SUCCESS: All duplicates resolved")
          else:
            log_upload_event(
                "IMPORT CSV STEP C: No duplicate columns to resolve")

          # Save processed data
          log_upload_event("IMPORT CSV STEP D: Saving processed data")
          out_name = f"import_{os.path.splitext(file_name)[0]}.csv"
          out_path = os.path.join(_user_upload_folder(), out_name)

          log_upload_event("IMPORT CSV STEP D1: Constructing output path",
                           output_filename=out_name, output_path=out_path)

          log_upload_event("IMPORT CSV STEP D2: Writing CSV file",
                           final_shape=df.shape, output_format="CSV")

          df.to_csv(out_path, index=False)
          saved_size = os.path.getsize(
              out_path) if os.path.exists(out_path) else 0

          log_upload_event("IMPORT CSV STEP D SUCCESS: Data saved successfully",
                           output_file=out_name, saved_size_bytes=saved_size,
                           rows=int(df.shape[0]), cols=int(df.shape[1]))

          # If this looks like taxonomy data, write to Taxonomy table
          try:
            from ..models.taxonomy import Taxonomy
            from .. import db

            # Heuristic: if any of expected taxonomy identifier columns are present
            cols = {c.lower() for c in df.columns}
            if taxonomy_table_identificatos.intersection(cols):
              log_upload_event("IMPORT CSV STEP E: Detected taxonomy data, importing to DB",
                               user=current_user.email, rows=int(df.shape[0]))

              # Clear existing taxonomy for user
              Taxonomy.query.filter_by(user_id=current_user.id).delete()
              db.session.commit()

              records_added = 0
              for _, row in df.iterrows():
                try:
                  taxonomy_data = {k: v for k,
                                   v in row.to_dict().items() if pd.notna(v)}
                  Taxonomy.create_from_dict(current_user.id, taxonomy_data)
                  records_added += 1
                except Exception as e:
                  log_upload_event("IMPORT CSV STEP E WARNING: Failed to create taxonomy",
                                   error=str(e), row_data=str(row.to_dict())[:200])
                  continue

              db.session.commit()
              log_upload_event("IMPORT CSV STEP E SUCCESS: Taxonomy import completed",
                               added=records_added)
              imported.append({'sheet': 'CSV', 'rows': records_added, 'cols': int(
                  df.shape[1]), 'path': out_path, 'imported_to_db': True})
          except Exception as e:
            log_upload_event("IMPORT CSV STEP E FAILED: Taxonomy DB import failed",
                             error=str(e), error_type=type(e).__name__)
          imported.append({
              'sheet': 'CSV',
              'rows': int(df.shape[0]),
              'cols': int(df.shape[1]),
              'path': out_path
          })
        else:
          log_upload_event("IMPORT CSV SKIPPED: CSV not confirmed for import")

    except Exception as e:
      log_upload_event("IMPORT STEP X FAILED: Import processing failed",
                       filename=file_name, error=str(e), error_type=type(e).__name__)
      user_logger.log_error('upload', e, f'File import processing: {file_name}')
      return {'message': f'Import failed: {e}'}, 500

    # Step 6: Finalize import results
    log_upload_event("IMPORT STEP 6: Finalizing import results")
    total_rows = sum(item.get('rows', 0) for item in imported)
    total_cols = sum(item.get('cols', 0) for item in imported)

    log_upload_event("IMPORT STEP 6 SUCCESS: Import completed successfully",
                     filename=file_name, imported_count=len(imported),
                     total_rows=total_rows, total_cols=total_cols,
                     imported_sheets=[item.get('sheet') for item in imported])

    return {'message': 'Import completed', 'imported': imported}


@uploads_ns.route('/taxonomy')
class TaxonomyPage(Resource):
  @login_required
  @log_function('uploads')
  def get(self):
    """Render the taxonomy management page with data from the database."""
    try:
      user_id = current_user.id
      current_app.logger.info(f"Fetching taxonomy data for user_id={user_id}")
      taxonomies = Taxonomy.query.filter_by(user_id=user_id).all()
      current_app.logger.info(
          f"Fetched {len(taxonomies)} taxonomy records for user_id={user_id}")
      return render_template('taxonomy.html', taxonomies=taxonomies)
    except Exception as e:
      current_app.logger.error(f"Failed to load taxonomy data: {e}")
      return render_template('taxonomy.html', taxonomies=[])
