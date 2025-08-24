"""
Patient model for MVA2 application

Handles patient clinical data, demographics, and treatment information
for multiple myeloma research with comprehensive data validation.
"""

from datetime import datetime
from .. import db
from sqlalchemy.dialects.postgresql import JSON
import json


class Patient(db.Model):
  """
  Patient model for storing clinical and demographic data

  Features:
  - Comprehensive patient demographics
  - Disease characteristics and staging
  - FISH indicators and genomic markers
  - Laboratory values and treatment data
  - User-specific data isolation
  """

  __tablename__ = 'patients'

  # Primary identification
  id = db.Column(db.Integer, primary_key=True)
  patient_id = db.Column(db.String(50), nullable=False, index=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

  # Demographics
  age = db.Column(db.Float, nullable=True)
  gender = db.Column(db.String(20), nullable=True)
  race = db.Column(db.String(50), nullable=True)
  ethnicity = db.Column(db.String(50), nullable=True)
  weight_kg = db.Column(db.Float, nullable=True)
  height_m = db.Column(db.Float, nullable=True)
  bmi = db.Column(db.Float, nullable=True)
  smoking = db.Column(db.String(20), nullable=True)
  smoking_status = db.Column(db.String(50), nullable=True)

  # Disease characteristics
  igg = db.Column(db.Float, nullable=True)
  iga = db.Column(db.Float, nullable=True)
  biclonal = db.Column(db.String(10), nullable=True)
  lightchain = db.Column(db.String(20), nullable=True)
  igh_rearrangement = db.Column(db.String(50), nullable=True)
  hr_mutations = db.Column(db.String(100), nullable=True)
  ultrahr_mutations = db.Column(db.String(100), nullable=True)
  imwg_hr = db.Column(db.String(20), nullable=True)
  functional_hr = db.Column(db.String(20), nullable=True)

  # Disease staging
  iss = db.Column(db.String(10), nullable=True)
  riss = db.Column(db.String(10), nullable=True)
  beta2microglobulin = db.Column(db.Float, nullable=True)
  creatinine = db.Column(db.Float, nullable=True)
  albumin = db.Column(db.Float, nullable=True)

  # FISH indicators
  monosomy_3 = db.Column(db.Boolean, nullable=True)
  gain_3 = db.Column(db.Boolean, nullable=True)
  gain_5 = db.Column(db.Boolean, nullable=True)
  gain_7 = db.Column(db.Boolean, nullable=True)
  monosomy_9 = db.Column(db.Boolean, nullable=True)
  gain_9 = db.Column(db.Boolean, nullable=True)
  monosomy_11 = db.Column(db.Boolean, nullable=True)
  gain_11 = db.Column(db.Boolean, nullable=True)
  monosomy_13 = db.Column(db.Boolean, nullable=True)
  gain_15 = db.Column(db.Boolean, nullable=True)
  monosomy_17 = db.Column(db.Boolean, nullable=True)
  gain_19 = db.Column(db.Boolean, nullable=True)
  gain_21 = db.Column(db.Boolean, nullable=True)
  del_13q = db.Column(db.Boolean, nullable=True)
  t_11_14 = db.Column(db.Boolean, nullable=True)
  t_4_14 = db.Column(db.Boolean, nullable=True)
  t_14_16 = db.Column(db.Boolean, nullable=True)
  t_14_20 = db.Column(db.Boolean, nullable=True)
  gain_1q = db.Column(db.Boolean, nullable=True)
  del_1p32 = db.Column(db.Boolean, nullable=True)
  del_17p = db.Column(db.Boolean, nullable=True)
  abnorm_6q21 = db.Column(db.Boolean, nullable=True)
  t_12_22 = db.Column(db.Boolean, nullable=True)

  # Genomic markers
  tp53_mutation = db.Column(db.Boolean, nullable=True)
  rb1_deletion = db.Column(db.Boolean, nullable=True)
  myc_rearrangement = db.Column(db.Boolean, nullable=True)
  cyclin_d1 = db.Column(db.Float, nullable=True)
  cyclin_d2 = db.Column(db.Float, nullable=True)
  cyclin_d3 = db.Column(db.Float, nullable=True)
  maf_rearrangement = db.Column(db.Boolean, nullable=True)

  # Laboratory values
  ldh = db.Column(db.Float, nullable=True)
  hemoglobin = db.Column(db.Float, nullable=True)
  platelet_count = db.Column(db.Float, nullable=True)
  neutrophil_count = db.Column(db.Float, nullable=True)
  lymphocyte_count = db.Column(db.Float, nullable=True)

  # Treatment and transplantation
  induction_therapy = db.Column(db.String(100), nullable=True)
  melphalan_mg_per_m2 = db.Column(db.Float, nullable=True)
  first_transplant_date = db.Column(db.Date, nullable=True)
  date_engraftment = db.Column(db.Date, nullable=True)
  months_first_transplant = db.Column(db.Float, nullable=True)
  second_transplant_date = db.Column(db.Date, nullable=True)
  months_second_transplant = db.Column(db.Float, nullable=True)

  # Outcomes and survival
  duration_pfs = db.Column(db.Float, nullable=True)  # Primary duration variable
  # Primary event indicator\n    duration_survival = db.Column(db.Float, nullable=True)
  pfs_status = db.Column(db.Boolean, nullable=True)
  death_status = db.Column(db.Boolean, nullable=True)

  # Relapse information
  relapse_date = db.Column(db.Date, nullable=True)
  relapse_months_first_transplant = db.Column(db.Float, nullable=True)
  relapse_months_second_transplant = db.Column(db.Float, nullable=True)
  death_date = db.Column(db.Date, nullable=True)
  death_months_first_transplant = db.Column(db.Float, nullable=True)
  death_months_second_transplant = db.Column(db.Float, nullable=True)

  # Comorbidities and adverse events
  es = db.Column(db.Boolean, nullable=True)
  es_noninfectious_fever = db.Column(db.Boolean, nullable=True)
  es_noninfectious_diarrhea = db.Column(db.Boolean, nullable=True)
  es_rash = db.Column(db.Boolean, nullable=True)

  # Medications (antibiotics, antifungals, antivirals)
  ciprofloxacin = db.Column(db.Boolean, nullable=True)
  ciprofloxacin_engraftment = db.Column(db.Boolean, nullable=True)
  levofloxacin = db.Column(db.Boolean, nullable=True)
  levofloxacin_engraftment = db.Column(db.Boolean, nullable=True)
  moxifloxacin = db.Column(db.Boolean, nullable=True)
  moxifloxacin_engraftment = db.Column(db.Boolean, nullable=True)
  amoxicillin = db.Column(db.Boolean, nullable=True)
  amoxicillin_engraftment = db.Column(db.Boolean, nullable=True)
  ampicillin = db.Column(db.Boolean, nullable=True)
  ampicillin_engraftment = db.Column(db.Boolean, nullable=True)
  cefepime = db.Column(db.Boolean, nullable=True)
  cefepime_engraftment = db.Column(db.Boolean, nullable=True)
  cefazolin = db.Column(db.Boolean, nullable=True)
  cefazolin_engraftment = db.Column(db.Boolean, nullable=True)
  azithromycin = db.Column(db.Boolean, nullable=True)
  azithromycin_engraftment = db.Column(db.Boolean, nullable=True)
  trimethoprim_sulfamethoxazole = db.Column(db.Boolean, nullable=True)
  trimethoprim_sulfamethoxazole_engraftment = db.Column(
      db.Boolean, nullable=True)
  clindamycin = db.Column(db.Boolean, nullable=True)
  clindamycin_engraftment = db.Column(db.Boolean, nullable=True)
  metronidazole = db.Column(db.Boolean, nullable=True)
  metronidazole_engraftment = db.Column(db.Boolean, nullable=True)
  piperacillin_tazobactam = db.Column(db.Boolean, nullable=True)
  piperacillin_tazobactam_engraftment = db.Column(db.Boolean, nullable=True)
  vancomycin_iv = db.Column(db.Boolean, nullable=True)
  vancomycin_iv_engraftment = db.Column(db.Boolean, nullable=True)
  vancomycin_po = db.Column(db.Boolean, nullable=True)
  vancomycin_po_engraftment = db.Column(db.Boolean, nullable=True)
  fluconazole = db.Column(db.Boolean, nullable=True)
  fluconazole_engraftment = db.Column(db.Boolean, nullable=True)
  acyclovir = db.Column(db.Boolean, nullable=True)
  valacyclovir = db.Column(db.Boolean, nullable=True)

  # Dates and follow-up
  last_contact_date = db.Column(db.Date, nullable=True)
  start_date = db.Column(db.Date, nullable=True)
  end_date = db.Column(db.Date, nullable=True)
  start_date_engraftment = db.Column(db.Date, nullable=True)
  end_date_engraftment = db.Column(db.Date, nullable=True)

  # Metadata
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
  updated_at = db.Column(
      db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Additional data as JSON for flexibility
  additional_data = db.Column(JSON, nullable=True)

  def __repr__(self):
    return f'<Patient {self.patient_id}>'

  def __init__(self, **kwargs):
    """Initialize patient with data validation"""
    super(Patient, self).__init__(**kwargs)
    self.validate_data()

  def validate_data(self):
    """Validate patient data according to clinical standards"""
    # Age validation
    if self.age is not None and (self.age < 0 or self.age > 120):
      raise ValueError("Age must be between 0 and 120")

    # BMI calculation if height and weight are provided
    if self.height_m and self.weight_kg and not self.bmi:
      self.bmi = self.weight_kg / (self.height_m ** 2)

    # Laboratory value validation
    if self.creatinine is not None and (self.creatinine < 0.1 or self.creatinine > 20.0):
      raise ValueError("Creatinine value out of valid range")

    if self.albumin is not None and (self.albumin < 1.0 or self.albumin > 6.0):
      raise ValueError("Albumin value out of valid range")

    if self.beta2microglobulin is not None and (self.beta2microglobulin < 0.5 or self.beta2microglobulin > 50.0):
      raise ValueError("Beta-2 microglobulin value out of valid range")

  def get_demographics_group(self):
    """Get demographic grouping for analysis"""
    groups = []

    # Age stratification
    if self.age is not None:
      if self.age < 65:
        groups.append('age_under_65')
      elif self.age <= 75:
        groups.append('age_65_75')
      else:
        groups.append('age_over_75')

    # BMI categories
    if self.bmi is not None:
      if self.bmi < 18.5:
        groups.append('underweight')
      elif self.bmi < 25:
        groups.append('normal_weight')
      elif self.bmi < 30:
        groups.append('overweight')
      else:
        groups.append('obese')

    return groups

  def get_fish_risk_group(self):
    """Determine FISH-based risk stratification"""
    high_risk_indicators = [
        self.del_17p, self.t_4_14, self.t_14_16, self.t_14_20, self.gain_1q
    ]

    intermediate_risk_indicators = [
        self.del_13q, self.monosomy_13, self.t_11_14
    ]

    if any(high_risk_indicators):
      return 'high_risk'
    elif any(intermediate_risk_indicators):
      return 'intermediate_risk'
    else:
      return 'standard_risk'

  def get_disease_stage_group(self):
    """Get disease staging group (ISS/R-ISS)"""
    if self.riss:
      return f"riss_{self.riss}"
    elif self.iss:
      return f"iss_{self.iss}"
    else:
      return 'unknown_stage'

  def has_complete_survival_data(self):
    """Check if patient has complete survival data for analysis"""
    return (self.duration_pfs is not None and
            self.pfs_status is not None and
            self.duration_pfs > 0)

  def get_analysis_variables(self, variable_groups=None):
    """Get patient data as dictionary for analysis"""
    data = {}

    # Always include core survival data
    data['patient_id'] = self.patient_id
    data['duration_pfs'] = self.duration_pfs
    data['pfs_status'] = self.pfs_status
    data['duration_survival'] = self.duration_survival
    data['death_status'] = self.death_status

    # Include variable groups if specified
    if not variable_groups:
      variable_groups = ['demographics', 'disease_characteristics',
                         'fish_indicators', 'laboratory_values']

    if 'demographics' in variable_groups:
      data.update({
          'age': self.age,
          'gender': self.gender,
          'race': self.race,
          'ethnicity': self.ethnicity,
          'bmi': self.bmi,
          'smoking_status': self.smoking_status
      })

    if 'disease_characteristics' in variable_groups:
      data.update({
          'igg': self.igg,
          'iga': self.iga,
          'biclonal': self.biclonal,
          'lightchain': self.lightchain,
          'igh_rearrangement': self.igh_rearrangement,
          'iss': self.iss,
          'riss': self.riss,
          'imwg_hr': self.imwg_hr,
          'functional_hr': self.functional_hr
      })

    if 'fish_indicators' in variable_groups:
      data.update({
          'monosomy_3': self.monosomy_3,
          'gain_3': self.gain_3,
          'gain_5': self.gain_5,
          'gain_7': self.gain_7,
          'monosomy_9': self.monosomy_9,
          'gain_9': self.gain_9,
          'monosomy_11': self.monosomy_11,
          'gain_11': self.gain_11,
          'monosomy_13': self.monosomy_13,
          'gain_15': self.gain_15,
          'monosomy_17': self.monosomy_17,
          'gain_19': self.gain_19,
          'gain_21': self.gain_21,
          'del_13q': self.del_13q,
          't_11_14': self.t_11_14,
          't_4_14': self.t_4_14,
          't_14_16': self.t_14_16,
          't_14_20': self.t_14_20,
          'gain_1q': self.gain_1q,
          'del_1p32': self.del_1p32,
          'del_17p': self.del_17p,
          'abnorm_6q21': self.abnorm_6q21,
          't_12_22': self.t_12_22
      })

    if 'laboratory_values' in variable_groups:
      data.update({
          'beta2microglobulin': self.beta2microglobulin,
          'creatinine': self.creatinine,
          'albumin': self.albumin,
          'ldh': self.ldh,
          'hemoglobin': self.hemoglobin,
          'platelet_count': self.platelet_count,
          'neutrophil_count': self.neutrophil_count,
          'lymphocyte_count': self.lymphocyte_count
      })

    # Remove None values
    return {k: v for k, v in data.items() if v is not None}

  def to_dict(self):
    """Convert patient to dictionary for API responses"""
    return {
        'id': self.id,
        'patient_id': self.patient_id,
        'age': self.age,
        'gender': self.gender,
        'race': self.race,
        'ethnicity': self.ethnicity,
        'duration_pfs': self.duration_pfs,
        'pfs_status': self.pfs_status,
        'fish_risk_group': self.get_fish_risk_group(),
        'disease_stage_group': self.get_disease_stage_group(),
        'has_complete_data': self.has_complete_survival_data(),
        'created_at': self.created_at.isoformat() if self.created_at else None
    }

  @staticmethod
  def create_from_dict(user_id, patient_data):
    """Create patient from dictionary data with validation"""
    # Map column names using fuzzy matching if needed
    from app.utils.data_mapping import map_patient_columns
    mapped_data = map_patient_columns(patient_data)

    patient = Patient(user_id=user_id, **mapped_data)
    db.session.add(patient)
    db.session.commit()
    return patient

  @staticmethod
  def bulk_create_from_dataframe(user_id, df):
    """Create multiple patients from pandas DataFrame"""
    patients = []
    for _, row in df.iterrows():
      try:
        patient_data = row.to_dict()
        patient = Patient.create_from_dict(user_id, patient_data)
        patients.append(patient)
      except Exception as e:
        current_app.logger.error(f"Error creating patient: {e}")
        continue

    return patients
