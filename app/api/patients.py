"""
Patient data API endpoints for MVA2 application

Handles patient data CRUD operations, filtering, and clinical data management.
"""

import traceback
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_login import login_required, current_user
from sqlalchemy import and_, or_

from app.models.patient import Patient
from app import db
from app.utils.validators import validate_patient_data
from app.utils.data_export import export_patients_to_csv
from app.utils.logging_utils import log_function

patients_ns = Namespace('patients', description='Patient data operations')

# Response models
patient_model = patients_ns.model('Patient', {
    'id': fields.Integer(description='Database ID'),
    'patient_id': fields.String(description='Patient identifier'),
    'age': fields.Integer(description='Patient age'),
    'sex': fields.String(description='Patient sex'),
    'race': fields.String(description='Patient race'),
    'diagnosis_date': fields.DateTime(description='Diagnosis date'),
    'stage': fields.String(description='Disease stage'),
    'survival_months': fields.Float(description='Survival time in months'),
    'survival_status': fields.Integer(description='Survival status (0=alive, 1=dead)'),
    'created_at': fields.DateTime(description='Record creation date')
})

patient_list_model = patients_ns.model('PatientList', {
    'patients': fields.List(fields.Nested(patient_model)),
    'total_count': fields.Integer(description='Total number of patients'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Records per page'),
    'pages': fields.Integer(description='Total pages')
})

# Request models
patient_create_model = patients_ns.model('PatientCreate', {
    'patient_id': fields.String(required=True, description='Patient identifier'),
    'age': fields.Integer(description='Patient age'),
    'sex': fields.String(description='Patient sex'),
    'race': fields.String(description='Patient race'),
    'diagnosis_date': fields.DateTime(description='Diagnosis date'),
    'stage': fields.String(description='Disease stage'),
    'survival_months': fields.Float(description='Survival time in months'),
    'survival_status': fields.Integer(description='Survival status'),
    'fish_data': fields.Raw(description='FISH analysis data'),
    'laboratory_values': fields.Raw(description='Laboratory test results'),
    'treatment_data': fields.Raw(description='Treatment information'),
    'metadata': fields.Raw(description='Additional metadata')
})


@patients_ns.route('/')
class PatientList(Resource):
  """Patient list and creation endpoint"""

  @patients_ns.doc('list_patients')
  @patients_ns.marshal_with(patient_list_model)
  @patients_ns.param('page', 'Page number', type=int, default=1)
  @patients_ns.param('per_page', 'Records per page', type=int, default=50)
  @patients_ns.param('search', 'Search term', type=str)
  @patients_ns.param('stage', 'Disease stage filter', type=str)
  @patients_ns.param('sex', 'Sex filter', type=str)
  @patients_ns.param('race', 'Race filter', type=str)
  @login_required
  @log_function('patients')
  def get(self):
    """Get list of patients with optional filtering"""
    try:
      # Get query parameters
      page = request.args.get('page', 1, type=int)
      per_page = min(request.args.get('per_page', 50, type=int), 100)
      search = request.args.get('search', '')
      stage_filter = request.args.get('stage', '')
      sex_filter = request.args.get('sex', '')
      race_filter = request.args.get('race', '')

      # Base query for user's patients
      query = Patient.query.filter_by(user_id=current_user.id)

      # Apply search filter
      if search:
        # Sanitize search term to prevent SQL injection - escape % and _ for LIKE
        safe_search = search.replace('%', '\\%').replace('_', '\\_')
        search_term = f"%{safe_search}%"
        query = query.filter(
            or_(
                Patient.patient_id.ilike(search_term, escape='\\'),
                Patient.race.ilike(search_term, escape='\\'),
                Patient.gender.ilike(search_term, escape='\\')
            )
        )

      # Apply specific filters
      if stage_filter:
        # Older code used 'stage' field; model contains 'iss' and 'riss'
        query = query.filter(
            or_(Patient.iss == stage_filter, Patient.riss == stage_filter))

      if sex_filter:
        # Model uses 'gender' field
        query = query.filter(Patient.gender == sex_filter)

      if race_filter:
        query = query.filter(Patient.race == race_filter)

      # Paginate results
      pagination = query.paginate(page=page, per_page=per_page, error_out=False)

      return {
          'patients': [patient.to_dict() for patient in pagination.items],
          'total_count': pagination.total,
          'page': page,
          'per_page': per_page,
          'pages': pagination.pages
      }

    except Exception as e:
      traceback.print_exc()
      current_app.logger.error(f"Error fetching patients: {e}")
      return {'message': 'Failed to fetch patients'}, 500

  @patients_ns.doc('create_patient')
  @patients_ns.expect(patient_create_model)
  @patients_ns.marshal_with(patient_model)
  @login_required
  @log_function('patients')
  def post(self):
    """Create a new patient record"""
    try:
      data = request.get_json()

      # Validate required fields
      if not data.get('patient_id'):
        return {'message': 'Patient ID is required'}, 400

      # Check if patient already exists for this user
      existing = Patient.query.filter_by(
          user_id=current_user.id,
          patient_id=data['patient_id']
      ).first()

      if existing:
        return {'message': 'Patient with this ID already exists'}, 409

      # Validate patient data
      validation_errors = validate_patient_data(data)
      if validation_errors:
        return {'message': 'Validation failed', 'errors': validation_errors}, 400

      # Create new patient
      patient = Patient(
          user_id=current_user.id,
          patient_id=data['patient_id'],
          age=data.get('age'),
          sex=data.get('sex'),
          race=data.get('race'),
          diagnosis_date=data.get('diagnosis_date'),
          stage=data.get('stage'),
          survival_months=data.get('survival_months'),
          survival_status=data.get('survival_status'),
          fish_data=data.get('fish_data'),
          laboratory_values=data.get('laboratory_values'),
          treatment_data=data.get('treatment_data'),
          metadata=data.get('metadata')
      )

      db.session.add(patient)
      db.session.commit()

      current_app.logger.info(
          f"Created patient {patient.patient_id} for user {current_user.email}")

      return patient.to_dict(), 201

    except Exception as e:
      db.session.rollback()
      current_app.logger.error(f"Error creating patient: {e}")
      return {'message': 'Failed to create patient'}, 500


@patients_ns.route('/<int:patient_id>')
class PatientDetail(Resource):
  """Individual patient operations"""

  @patients_ns.doc('get_patient')
  @patients_ns.marshal_with(patient_model)
  @login_required
  @log_function('patients')
  def get(self, patient_id):
    """Get specific patient by ID"""
    patient = Patient.query.filter_by(
        id=patient_id,
        user_id=current_user.id
    ).first()

    if not patient:
      return {'message': 'Patient not found'}, 404

    return patient.to_dict()

  @patients_ns.doc('update_patient')
  @patients_ns.expect(patient_create_model)
  @patients_ns.marshal_with(patient_model)
  @login_required
  @log_function('patients')
  def put(self, patient_id):
    """Update specific patient"""
    try:
      patient = Patient.query.filter_by(
          id=patient_id,
          user_id=current_user.id
      ).first()

      if not patient:
        return {'message': 'Patient not found'}, 404

      data = request.get_json()

      # Validate data
      validation_errors = validate_patient_data(data)
      if validation_errors:
        return {'message': 'Validation failed', 'errors': validation_errors}, 400

      # Update fields
      for field in ['age', 'sex', 'race', 'diagnosis_date', 'stage',
                    'survival_months', 'survival_status', 'fish_data',
                    'laboratory_values', 'treatment_data', 'metadata']:
        if field in data:
          setattr(patient, field, data[field])

      db.session.commit()

      return patient.to_dict()

    except Exception as e:
      db.session.rollback()
      current_app.logger.error(f"Error updating patient: {e}")
      return {'message': 'Failed to update patient'}, 500

  @patients_ns.doc('delete_patient')
  @login_required
  @log_function('patients')
  def delete(self, patient_id):
    """Delete specific patient"""
    try:
      patient = Patient.query.filter_by(
          id=patient_id,
          user_id=current_user.id
      ).first()

      if not patient:
        return {'message': 'Patient not found'}, 404

      db.session.delete(patient)
      db.session.commit()

      return {'message': 'Patient deleted successfully'}

    except Exception as e:
      db.session.rollback()
      current_app.logger.error(f"Error deleting patient: {e}")
      return {'message': 'Failed to delete patient'}, 500


@patients_ns.route('/bulk')
class PatientBulk(Resource):
  """Bulk patient operations"""

  @patients_ns.doc('bulk_create_patients')
  @login_required
  @log_function('patients')
  def post(self):
    """Bulk create patients from uploaded data"""
    try:
      data = request.get_json()

      if not data or 'patients' not in data:
        return {'message': 'Patient data required'}, 400

      created_patients = []
      errors = []

      for i, patient_data in enumerate(data['patients']):
        try:
          # Validate patient data
          validation_errors = validate_patient_data(patient_data)
          if validation_errors:
            errors.append({
                'row': i + 1,
                'errors': validation_errors
            })
            continue

          # Check for duplicates
          existing = Patient.query.filter_by(
              user_id=current_user.id,
              patient_id=patient_data['patient_id']
          ).first()

          if existing:
            errors.append({
                'row': i + 1,
                'errors': [f"Patient {patient_data['patient_id']} already exists"]
            })
            continue

          # Create patient
          patient = Patient(user_id=current_user.id, **patient_data)
          db.session.add(patient)
          created_patients.append(patient)

        except Exception as e:
          errors.append({
              'row': i + 1,
              'errors': [str(e)]
          })

      db.session.commit()

      return {
          'message': f'Created {len(created_patients)} patients',
          'created_count': len(created_patients),
          'error_count': len(errors),
          'errors': errors
      }

    except Exception as e:
      db.session.rollback()
      current_app.logger.error(f"Error in bulk create: {e}")
      return {'message': 'Bulk creation failed'}, 500


@patients_ns.route('/export')
class PatientExport(Resource):
  """Patient data export"""

  @patients_ns.doc('export_patients')
  @patients_ns.param('format', 'Export format (csv, excel)', default='csv')
  @patients_ns.param('include_fields', 'Comma-separated list of fields to include')
  @login_required
  @log_function('patients')
  def get(self):
    """Export patient data"""
    try:
      format_type = request.args.get('format', 'csv')
      include_fields = request.args.get('include_fields', '').split(
          ',') if request.args.get('include_fields') else None

      # Get user's patients
      patients = Patient.query.filter_by(user_id=current_user.id).all()

      if format_type == 'csv':
        return export_patients_to_csv(patients, include_fields)
      else:
        return {'message': 'Unsupported export format'}, 400

    except Exception as e:
      current_app.logger.error(f"Error exporting patients: {e}")
      return {'message': 'Export failed'}, 500


@patients_ns.route('/statistics')
class PatientStatistics(Resource):
  """Patient cohort statistics"""

  @patients_ns.doc('patient_statistics')
  @login_required
  @log_function('patients')
  def get(self):
    """Get statistics about patient cohort"""
    try:
      patients = Patient.query.filter_by(user_id=current_user.id).all()

      if not patients:
        return {
            'total_patients': 0,
            'demographics': {},
            'survival': {},
            'clinical': {}
        }

      # Calculate statistics
      total = len(patients)

      # Demographics
      sex_counts = {}
      race_counts = {}
      age_values = []

      # Clinical
      stage_counts = {}
      survival_values = []
      death_count = 0

      for patient in patients:
        # Demographics
        if patient.sex:
          sex_counts[patient.sex] = sex_counts.get(patient.sex, 0) + 1
        if patient.race:
          race_counts[patient.race] = race_counts.get(patient.race, 0) + 1
        if patient.age:
          age_values.append(patient.age)

        # Clinical
        if patient.stage:
          stage_counts[patient.stage] = stage_counts.get(patient.stage, 0) + 1
        if patient.survival_months:
          survival_values.append(patient.survival_months)
        if patient.survival_status == 1:
          death_count += 1

      return {
          'total_patients': total,
          'demographics': {
              'sex_distribution': sex_counts,
              'race_distribution': race_counts,
              'age_mean': sum(age_values) / len(age_values) if age_values else 0,
              'age_range': [min(age_values), max(age_values)] if age_values else [0, 0]
          },
          'survival': {
              'total_deaths': death_count,
              'survival_rate': (total - death_count) / total if total > 0 else 0,
              'median_survival': sorted(survival_values)[len(survival_values)//2] if survival_values else 0
          },
          'clinical': {
              'stage_distribution': stage_counts
          }
      }

    except Exception as e:
      current_app.logger.error(f"Error calculating statistics: {e}")
      return {'message': 'Failed to calculate statistics'}, 500
