"""
Analysis models for MVA2 application

Handles analysis results, statistical computations, and saved analysis workflows
for biomedical research on multiple myeloma and microbiome data.
"""

from datetime import datetime
from .. import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import func
from enum import Enum


class AnalysisType(Enum):
  """Types of statistical analyses supported"""
  SURVIVAL = "survival"
  COX_REGRESSION = "cox_regression"
  KAPLAN_MEIER = "kaplan_meier"
  RMST = "rmst"
  WILCOXON = "wilcoxon"
  MANN_WHITNEY = "mann_whitney"
  KRUSKAL_WALLIS = "kruskal_wallis"
  CORRELATION = "correlation"
  DIFFERENTIAL_ABUNDANCE = "differential_abundance"
  DIVERSITY = "diversity"
  PCA = "pca"
  PERMANOVA = "permanova"
  VOLCANO_PLOT = "volcano_plot"
  HEATMAP = "heatmap"


class AnalysisStatus(Enum):
  """Analysis execution status"""
  PENDING = "pending"
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"
  CANCELLED = "cancelled"


class Analysis(db.Model):
  """
  Analysis model for storing analysis configurations and results

  Features:
  - Multiple analysis types (survival, statistical, microbiome)
  - User-specific analysis isolation
  - Analysis configuration and parameters
  - Results storage with visualization data
  - Execution tracking and status
  """

  __tablename__ = 'analyses'

  # Primary identification
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  name = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text, nullable=True)

  # Analysis type and status
  analysis_type = db.Column(db.Enum(AnalysisType), nullable=False)
  status = db.Column(db.Enum(AnalysisStatus), default=AnalysisStatus.PENDING)

  # Configuration and parameters
  configuration = db.Column(JSON, nullable=False)  # Analysis parameters
  grouping_strategy = db.Column(db.String(100), nullable=True)
  grouping_parameters = db.Column(JSON, nullable=True)

  # Data selection
  patient_selection = db.Column(JSON, nullable=True)  # Patient IDs or criteria
  taxonomy_selection = db.Column(JSON, nullable=True)  # Taxonomy filters
  variable_selection = db.Column(JSON, nullable=True)  # Variables to analyze

  # Results and outputs
  results = db.Column(JSON, nullable=True)  # Statistical results
  visualization_data = db.Column(JSON, nullable=True)  # Plot data
  report_data = db.Column(JSON, nullable=True)  # Publication-ready data

  # Execution information
  execution_time = db.Column(db.Float, nullable=True)  # Seconds
  error_message = db.Column(db.Text, nullable=True)
  warnings = db.Column(JSON, nullable=True)  # List of warning messages

  # Metadata
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
  updated_at = db.Column(
      db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  completed_at = db.Column(db.DateTime, nullable=True)

  # Publication and sharing
  is_public = db.Column(db.Boolean, default=False)
  publication_ready = db.Column(db.Boolean, default=False)
  tags = db.Column(JSON, nullable=True)  # List of tags

  # Relationships are defined in User model via backref

  def __init__(self, user_id=None, name=None, analysis_type=None,
               configuration=None, **kwargs):
    """Initialize a new Analysis instance"""
    super().__init__(**kwargs)
    if user_id:
      self.user_id = user_id
    if name:
      self.name = name
    if analysis_type:
      self.analysis_type = analysis_type
    if configuration:
      self.configuration = configuration

  def __repr__(self):
    return f'<Analysis {self.name} ({self.analysis_type.value})>'

  def start_execution(self):
    """Mark analysis as running"""
    self.status = AnalysisStatus.RUNNING
    self.updated_at = datetime.utcnow()
    db.session.commit()

  def complete_execution(self, results=None, visualization_data=None, execution_time=None):
    """Mark analysis as completed with results"""
    self.status = AnalysisStatus.COMPLETED
    self.completed_at = datetime.utcnow()

    if results:
      self.results = results
    if visualization_data:
      self.visualization_data = visualization_data
    if execution_time:
      self.execution_time = execution_time

    db.session.commit()

  def fail_execution(self, error_message, warnings=None):
    """Mark analysis as failed with error details"""
    self.status = AnalysisStatus.FAILED
    self.error_message = error_message
    if warnings:
      self.warnings = warnings
    db.session.commit()

  def get_configuration(self):
    """Get analysis configuration with defaults"""
    config = self.configuration or {}

    # Add default configurations based on analysis type
    defaults = self._get_default_configuration()
    for key, value in defaults.items():
      if key not in config:
        config[key] = value

    return config

  def _get_default_configuration(self):
    """Get default configuration for analysis type"""
    defaults = {
        AnalysisType.COX_REGRESSION: {
            'alpha': 0.05,
            'penalizer': 0.01,
            'l1_ratio': 0.0
        },
        AnalysisType.KAPLAN_MEIER: {
            'alpha': 0.05,
            'confidence_interval': 0.95
        },
        AnalysisType.RMST: {
            'tau': None,  # Will be set to max follow-up time
            'alpha': 0.05
        },
        AnalysisType.WILCOXON: {
            'alpha': 0.05,
            'alternative': 'two-sided'
        },
        AnalysisType.CORRELATION: {
            'method': 'spearman',
            'alpha': 0.05
        },
        AnalysisType.PCA: {
            'n_components': None,
            'scaling': 'standard'
        }
    }

    return defaults.get(self.analysis_type, {})

  def get_patient_data(self):
    """Get patient data for analysis based on selection criteria"""
    from app.models.patient import Patient

    if not self.patient_selection:
      # Return all patients for user
      return Patient.query.filter_by(user_id=self.user_id).all()

    # Apply selection criteria
    query = Patient.query.filter_by(user_id=self.user_id)

    if 'patient_ids' in self.patient_selection:
      query = query.filter(Patient.patient_id.in_(
          self.patient_selection['patient_ids']))

    if 'filters' in self.patient_selection:
      for filter_config in self.patient_selection['filters']:
        field = filter_config['field']
        operator = filter_config['operator']
        value = filter_config['value']

        if hasattr(Patient, field):
          column = getattr(Patient, field)
          if operator == 'eq':
            query = query.filter(column == value)
          elif operator == 'gt':
            query = query.filter(column > value)
          elif operator == 'lt':
            query = query.filter(column < value)
          elif operator == 'in':
            query = query.filter(column.in_(value))

    return query.all()

  def get_microbiome_data(self):
    """Get microbiome data for analysis"""
    from app.models.taxonomy import BrackenResult

    patients = self.get_patient_data()
    patient_ids = [p.patient_id for p in patients]

    query = BrackenResult.query.filter(
        BrackenResult.user_id == self.user_id,
        BrackenResult.patient_id.in_(patient_ids)
    )

    # Apply taxonomy selection
    if self.taxonomy_selection:
      if 'taxonomy_ids' in self.taxonomy_selection:
        query = query.filter(
            BrackenResult.taxonomy_id.in_(
                self.taxonomy_selection['taxonomy_ids'])
        )

    return query.all()

  def generate_report_summary(self):
    """Generate summary for publication-ready report"""
    if not self.results:
      return None

    summary = {
        'analysis_type': self.analysis_type.value,
        'analysis_name': self.name,
        'execution_date': self.completed_at.isoformat() if self.completed_at else None,
        'n_patients': len(self.get_patient_data()) if self.patient_selection else 0,
        'configuration': self.get_configuration(),
        'key_results': self._extract_key_results()
    }

    return summary

  def _extract_key_results(self):
    """Extract key results based on analysis type"""
    if not self.results:
      return {}

    key_results = {}

    if self.analysis_type == AnalysisType.COX_REGRESSION:
      if 'summary' in self.results:
        key_results['hazard_ratios'] = self.results['summary'].get(
            'hazard_ratios', {})
        key_results['p_values'] = self.results['summary'].get('p_values', {})
        key_results['concordance'] = self.results.get('concordance', None)

    elif self.analysis_type == AnalysisType.KAPLAN_MEIER:
      if 'median_survival' in self.results:
        key_results['median_survival'] = self.results['median_survival']
      if 'log_rank_test' in self.results:
        key_results['log_rank_p_value'] = self.results['log_rank_test'].get(
            'p_value')

    elif self.analysis_type == AnalysisType.RMST:
      if 'rmst_difference' in self.results:
        key_results['rmst_difference'] = self.results['rmst_difference']
        key_results['rmst_p_value'] = self.results.get('rmst_p_value')

    return key_results

  def to_dict(self, include_results=True):
    """Convert analysis to dictionary for API responses"""
    data = {
        'id': self.id,
        'name': self.name,
        'description': self.description,
        'analysis_type': self.analysis_type.value,
        'status': self.status.value,
        'configuration': self.configuration,
        'grouping_strategy': self.grouping_strategy,
        'execution_time': self.execution_time,
        'created_at': self.created_at.isoformat(),
        'updated_at': self.updated_at.isoformat(),
        'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        'is_public': self.is_public,
        'publication_ready': self.publication_ready,
        'tags': self.tags
    }

    if include_results:
      data.update({
          'results': self.results,
          'visualization_data': self.visualization_data,
          'report_summary': self.generate_report_summary()
      })

    if self.status == AnalysisStatus.FAILED:
      data['error_message'] = self.error_message
      data['warnings'] = self.warnings

    return data

  @staticmethod
  def create_analysis(user_id, name, analysis_type, configuration, **kwargs):
    """Create new analysis"""
    analysis = Analysis(
        user_id=user_id,
        name=name,
        analysis_type=analysis_type.value if isinstance(
            analysis_type, AnalysisType) else analysis_type,
        configuration=configuration,
        **kwargs
    )

    db.session.add(analysis)
    db.session.commit()
    return analysis

  @staticmethod
  def get_user_analyses(user_id, analysis_type=None, status=None):
    """Get analyses for a user with optional filtering"""
    query = Analysis.query.filter_by(user_id=user_id)

    if analysis_type:
      query = query.filter_by(analysis_type=analysis_type)

    if status:
      query = query.filter_by(status=status)

    return query.order_by(Analysis.created_at.desc()).all()


class SavedView(db.Model):
  """
  Saved view configurations for data visualization and analysis

  Features:
  - Custom data views and filters
  - Visualization configurations
  - Shareable view definitions
  """

  __tablename__ = 'saved_views'

  # Primary identification
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  name = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text, nullable=True)

  # View configuration
  # table, chart, heatmap, etc.
  view_type = db.Column(db.String(50), nullable=False)
  configuration = db.Column(JSON, nullable=False)

  # Data filters
  patient_filters = db.Column(JSON, nullable=True)
  taxonomy_filters = db.Column(JSON, nullable=True)
  variable_filters = db.Column(JSON, nullable=True)

  # Sharing and access
  is_public = db.Column(db.Boolean, default=False)
  shared_with = db.Column(JSON, nullable=True)  # List of User IDs

  # Metadata
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
  updated_at = db.Column(
      db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  last_accessed = db.Column(db.DateTime, nullable=True)
  access_count = db.Column(db.Integer, default=0)

  # Relationships
  user = db.relationship('User', backref='saved_view_objects')

  def __init__(self, user_id=None, name=None, view_type=None, **kwargs):
    """Initialize a new SavedView instance"""
    super().__init__(**kwargs)
    if user_id:
      self.user_id = user_id
    if name:
      self.name = name
    if view_type:
      self.view_type = view_type

  def __repr__(self):
    return f'<SavedView {self.name} ({self.view_type})>'

  def update_access(self):
    """Update access tracking"""
    self.last_accessed = datetime.utcnow()
    self.access_count += 1
    db.session.commit()

  def share_with_user(self, user_id):
    """Share view with another user"""
    if not self.shared_with:
      self.shared_with = []

    if user_id not in self.shared_with:
      self.shared_with.append(user_id)
      db.session.commit()

  def unshare_with_user(self, user_id):
    """Remove sharing with user"""
    if self.shared_with and user_id in self.shared_with:
      self.shared_with.remove(user_id)
      db.session.commit()

  def can_access(self, user_id):
    """Check if user can access this view"""
    return (
        self.user_id == user_id or
        self.is_public or
        (self.shared_with and user_id in self.shared_with)
    )

  def to_dict(self):
    """Convert to dictionary for API responses"""
    return {
        'id': self.id,
        'name': self.name,
        'description': self.description,
        'view_type': self.view_type,
        'configuration': self.configuration,
        'patient_filters': self.patient_filters,
        'taxonomy_filters': self.taxonomy_filters,
        'variable_filters': self.variable_filters,
        'is_public': self.is_public,
        'created_at': self.created_at.isoformat(),
        'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
        'access_count': self.access_count
    }

  @staticmethod
  def create_view(user_id, name, view_type, configuration, **kwargs):
    """Create new saved view"""
    view = SavedView(
        user_id=user_id,
        name=name,
        view_type=view_type,
        **kwargs
    )
    view.configuration = configuration

    db.session.add(view)
    db.session.commit()
    return view

  @staticmethod
  def get_accessible_views(user_id, view_type=None):
    """Get views accessible to user"""
    # For SQLite compatibility, we'll do simpler filtering
    # and check shared_with in Python code if needed
    query = SavedView.query.filter(
        db.or_(
            SavedView.user_id == user_id,
            SavedView.is_public == True
        )
    )

    if view_type:
      query = query.filter_by(view_type=view_type)

    return query.order_by(SavedView.updated_at.desc()).all()
