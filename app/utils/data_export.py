"""
Data export utilities for MVA2 application

Provides functions for exporting data in various formats (CSV, Excel, JSON).
"""

import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
from flask import Response
from app.utils.logging_utils import log_function


@log_function('data')
def export_patients_to_csv(patients, include_fields=None):
  """
  Export patient data to CSV format

  Args:
      patients (list): List of Patient objects
      include_fields (list): Optional list of fields to include

  Returns:
      Flask Response with CSV data
  """
  output = StringIO()

  if not patients:
    return Response(
        "No patients found",
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=patients_empty.csv'}
    )

  # Define default fields to export
  default_fields = [
      'patient_id', 'age', 'sex', 'race', 'diagnosis_date', 'stage',
      'survival_months', 'survival_status', 'created_at'
  ]

  # Use specified fields or defaults
  fields = include_fields if include_fields else default_fields

  writer = csv.writer(output)

  # Write header
  writer.writerow(fields)

  # Write patient data
  for patient in patients:
    row = []
    for field in fields:
      value = getattr(patient, field, None)

      # Format datetime fields
      if isinstance(value, datetime):
        value = value.isoformat()
      elif value is None:
        value = ''

      row.append(value)

    writer.writerow(row)

  output.seek(0)

  # Generate filename with timestamp
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  filename = f'patients_export_{timestamp}.csv'

  return Response(
      output.getvalue(),
      mimetype='text/csv',
      headers={'Content-Disposition': f'attachment; filename={filename}'}
  )


@log_function('data')
def export_taxonomy_to_csv(taxonomies, include_fields=None):
  """
  Export taxonomy data to CSV format

  Args:
      taxonomies (list): List of Taxonomy objects
      include_fields (list): Optional list of fields to include

  Returns:
      Flask Response with CSV data
  """
  output = StringIO()

  if not taxonomies:
    return Response(
        "No taxonomies found",
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=taxonomy_empty.csv'}
    )

  # Define default fields
  default_fields = [
      'taxonomy_id', 'domain', 'phylum', 'class_name', 'order', 'family',
      'genus', 'species', 'total_abundance', 'mean_abundance', 'prevalence'
  ]

  fields = include_fields if include_fields else default_fields

  writer = csv.writer(output)
  writer.writerow(fields)

  for taxonomy in taxonomies:
    row = []
    for field in fields:
      if field == 'class_name':
        value = getattr(taxonomy, 'class_name', None)
      else:
        value = getattr(taxonomy, field, None)

      if value is None:
        value = ''

      row.append(value)

    writer.writerow(row)

  output.seek(0)

  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  filename = f'taxonomy_export_{timestamp}.csv'

  return Response(
      output.getvalue(),
      mimetype='text/csv',
      headers={'Content-Disposition': f'attachment; filename={filename}'}
  )


@log_function('data')
def export_analysis_results_to_json(analysis):
  """
  Export analysis results to JSON format

  Args:
      analysis: Analysis object

  Returns:
      Flask Response with JSON data
  """
  if not analysis.results:
    return Response(
        json.dumps({'error': 'No results available'}),
        mimetype='application/json',
        headers={
            'Content-Disposition': 'attachment; filename=analysis_no_results.json'}
    )

  # Prepare export data
  export_data = {
      'analysis_info': {
          'name': analysis.name,
          'description': analysis.description,
          'analysis_type': analysis.analysis_type.value if analysis.analysis_type else None,
          'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
          'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
          'execution_time': analysis.execution_time
      },
      'configuration': analysis.configuration,
      'results': analysis.results,
      'visualization_data': analysis.visualization_data
  }

  # Generate filename
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  safe_name = ''.join(c for c in analysis.name if c.isalnum()
                      or c in (' ', '-', '_')).strip()
  filename = f'analysis_{safe_name}_{timestamp}.json'

  return Response(
      json.dumps(export_data, indent=2, default=str),
      mimetype='application/json',
      headers={'Content-Disposition': f'attachment; filename={filename}'}
  )


@log_function('data')
def export_bracken_results_to_csv(bracken_results):
  """
  Export Bracken results to CSV format

  Args:
      bracken_results (list): List of BrackenResult objects

  Returns:
      Flask Response with CSV data
  """
  output = StringIO()

  if not bracken_results:
    return Response(
        "No bracken results found",
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=bracken_empty.csv'}
    )

  fields = [
      'patient_id', 'taxonomy_id', 'abundance_pre', 'abundance_during',
      'abundance_post', 'delta_during_pre', 'delta_post_during', 'delta_post_pre'
  ]

  writer = csv.writer(output)
  writer.writerow(fields)

  for result in bracken_results:
    row = [
        result.patient_id,
        result.taxonomy_id,
        result.abundance_pre or '',
        result.abundance_during or '',
        result.abundance_post or '',
        result.delta_during_pre or '',
        result.delta_post_during or '',
        result.delta_post_pre or ''
    ]
    writer.writerow(row)

  output.seek(0)

  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  filename = f'bracken_results_{timestamp}.csv'

  return Response(
      output.getvalue(),
      mimetype='text/csv',
      headers={'Content-Disposition': f'attachment; filename={filename}'}
  )


@log_function('data')
def create_publication_report(analysis):
  """
  Create a publication-ready report for an analysis

  Args:
      analysis: Analysis object

  Returns:
      dict: Publication report data
  """
  report = {
      'title': f"Analysis Report: {analysis.name}",
      'generated_at': datetime.now().isoformat(),
      'analysis_details': {
          'type': analysis.analysis_type.value if analysis.analysis_type else 'unknown',
          'description': analysis.description,
          'execution_date': analysis.completed_at.isoformat() if analysis.completed_at else None,
          'execution_time_seconds': analysis.execution_time
      },
      'methodology': _get_methodology_text(analysis),
      'results': _format_results_for_publication(analysis),
      'statistical_summary': _create_statistical_summary(analysis),
      'figures': _prepare_figure_data(analysis)
  }

  return report


def _get_methodology_text(analysis):
  """Generate methodology text based on analysis type"""
  if not analysis.analysis_type:
    return "Methodology information not available."

  method_texts = {
      'cox_regression': "Cox proportional hazards regression analysis was performed to assess the relationship between variables and survival outcomes. The model was fitted using the partial likelihood method.",
      'kaplan_meier': "Kaplan-Meier survival analysis was performed to estimate survival probabilities. Log-rank test was used to compare survival curves between groups.",
      'rmst': "Restricted Mean Survival Time (RMST) analysis was performed to compare survival outcomes between groups while accounting for restricted follow-up time.",
      'wilcoxon': "Wilcoxon signed-rank test was performed to compare paired samples for significant differences.",
      'correlation': "Correlation analysis was performed to assess the strength and direction of relationships between variables."
  }

  return method_texts.get(analysis.analysis_type.value, "Analysis methodology details not available.")


def _format_results_for_publication(analysis):
  """Format analysis results for publication"""
  if not analysis.results:
    return "No results available."

  # This would be customized based on analysis type
  return analysis.results


def _create_statistical_summary(analysis):
  """Create statistical summary for publication"""
  summary = {
      'sample_size': 'N/A',
      'test_statistic': 'N/A',
      'p_value': 'N/A',
      'effect_size': 'N/A',
      'confidence_interval': 'N/A'
  }

  if analysis.results:
    # Extract common statistical measures
    if 'p_value' in analysis.results:
      summary['p_value'] = analysis.results['p_value']

    if 'sample_size' in analysis.results:
      summary['sample_size'] = analysis.results['sample_size']

    # Add more extraction logic based on analysis type

  return summary


def _prepare_figure_data(analysis):
  """Prepare figure data for publication"""
  figures = []

  if analysis.visualization_data:
    # Convert visualization data to publication format
    for viz_type, viz_data in analysis.visualization_data.items():
      figure = {
          'type': viz_type,
          'title': f"{analysis.name} - {viz_type.replace('_', ' ').title()}",
          'data': viz_data,
          'caption': f"Figure showing {viz_type.replace('_', ' ')} for {analysis.name}"
      }
      figures.append(figure)

  return figures
