"""
Taxonomy model for MVA2 application

Handles taxonomic classifications for microbiome data analysis
with hierarchical taxonomy structure and metadata.
"""

from datetime import datetime
from .. import db
from sqlalchemy.dialects.postgresql import JSON


class Taxonomy(db.Model):
  """
  Taxonomy model for microbiome taxonomic classifications

  Features:
  - Hierarchical taxonomy structure (Domain -> Species)
  - User-specific data isolation
  - Metadata and annotations
  - Abundance data tracking
  """

  __tablename__ = 'taxonomies'

  # Primary identification
  id = db.Column(db.Integer, primary_key=True)
  taxonomy_id = db.Column(db.String(100), nullable=False, index=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

  # ASV information
  asv = db.Column(db.String(100), nullable=True)

  # Taxonomic hierarchy
  domain = db.Column(db.String(100), nullable=True)
  phylum = db.Column(db.String(100), nullable=True)
  class_name = db.Column('class', db.String(
      100), nullable=True)  # 'class' is reserved keyword
  order = db.Column(db.String(100), nullable=True)
  family = db.Column(db.String(100), nullable=True)
  genus = db.Column(db.String(100), nullable=True)
  species = db.Column(db.String(100), nullable=True)

  # Full taxonomy string
  full_taxonomy = db.Column(db.Text, nullable=True)

  # Confidence and quality metrics
  classification_confidence = db.Column(db.Float, nullable=True)
  quality_score = db.Column(db.Float, nullable=True)

  # Abundance statistics (across all samples for this user)
  total_abundance = db.Column(db.Float, default=0.0)
  max_abundance = db.Column(db.Float, default=0.0)
  min_abundance = db.Column(db.Float, default=0.0)
  mean_abundance = db.Column(db.Float, default=0.0)
  # Percentage of samples where present
  prevalence = db.Column(db.Float, default=0.0)

  # Functional annotations
  functional_annotations = db.Column(JSON, nullable=True)

  # Metadata
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
  updated_at = db.Column(
      db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Additional metadata as JSON (attribute renamed to avoid SQLAlchemy reserved name)
  metadata_json = db.Column('metadata', JSON, nullable=True)

  def __init__(self, user_id=None, **kwargs):
    """Initialize a new Taxonomy instance"""
    super().__init__(**kwargs)
    if user_id:
      self.user_id = user_id

  def __repr__(self):
    return f'<Taxonomy {self.taxonomy_id}: {self.get_display_name()}>'

  def get_display_name(self):
    """Get the most specific taxonomic name available"""
    for level in ['species', 'genus', 'family', 'order', 'class_name', 'phylum', 'domain']:
      value = getattr(self, level)
      if value and value.strip():
        return value
    return self.taxonomy_id

  def get_full_lineage(self):
    """Get full taxonomic lineage as string"""
    lineage_parts = []
    levels = ['domain', 'phylum', 'class_name',
              'order', 'family', 'genus', 'species']

    for level in levels:
      value = getattr(self, level)
      if value and value.strip():
        lineage_parts.append(f"{level.replace('_name', '').title()}: {value}")

    return "; ".join(lineage_parts)

  def get_taxonomic_level(self):
    """Determine the most specific taxonomic level available"""
    levels = ['species', 'genus', 'family',
              'order', 'class_name', 'phylum', 'domain']

    for level in levels:
      value = getattr(self, level)
      if value and value.strip():
        return level.replace('_name', '')

    return 'unknown'

  def is_rare_taxon(self, prevalence_threshold=0.05):
    """Check if this is a rare taxon based on prevalence"""
    return self.prevalence < prevalence_threshold

  def is_abundant_taxon(self, abundance_threshold=0.01):
    """Check if this is an abundant taxon based on mean abundance"""
    return self.mean_abundance > abundance_threshold

  def update_abundance_stats(self, abundances):
    """Update abundance statistics from a list of abundance values"""
    if not abundances:
      return

    # Filter out zero/None values for statistics
    non_zero_abundances = [a for a in abundances if a and a > 0]

    self.total_abundance = sum(abundances)
    self.max_abundance = max(abundances) if abundances else 0
    self.min_abundance = min(non_zero_abundances) if non_zero_abundances else 0
    self.mean_abundance = sum(abundances) / len(abundances) if abundances else 0
    self.prevalence = len(non_zero_abundances) / \
        len(abundances) if abundances else 0

    db.session.commit()

  def get_functional_info(self):
    """Get functional annotation information"""
    if not self.functional_annotations:
      return {}
    return self.functional_annotations

  def add_functional_annotation(self, annotation_type, value):
    """Add functional annotation"""
    if not self.functional_annotations:
      self.functional_annotations = {}

    self.functional_annotations[annotation_type] = value
    db.session.commit()

  def to_dict(self):
    """Convert taxonomy to dictionary for API responses"""
    return {
        'id': self.id,
        'taxonomy_id': self.taxonomy_id,
        'asv': self.asv,
        'domain': self.domain,
        'phylum': self.phylum,
        'class': self.class_name,
        'order': self.order,
        'family': self.family,
        'genus': self.genus,
        'species': self.species,
        'display_name': self.get_display_name(),
        'full_lineage': self.get_full_lineage(),
        'taxonomic_level': self.get_taxonomic_level(),
        'total_abundance': self.total_abundance,
        'mean_abundance': self.mean_abundance,
        'prevalence': self.prevalence,
        'is_rare': self.is_rare_taxon(),
        'is_abundant': self.is_abundant_taxon(),
        'functional_annotations': self.functional_annotations,
        'created_at': self.created_at.isoformat() if self.created_at else None
    }

  @staticmethod
  def create_from_dict(user_id, taxonomy_data):
    """Create taxonomy from dictionary data"""
    # Map column names using fuzzy matching if needed
    from app.utils.data_mapping import map_taxonomy_columns
    mapped_data = map_taxonomy_columns(taxonomy_data)

    taxonomy = Taxonomy(user_id=user_id, **mapped_data)
    db.session.add(taxonomy)
    db.session.commit()
    return taxonomy

  @staticmethod
  def bulk_create_from_dataframe(user_id, df):
    """Create multiple taxonomies from pandas DataFrame"""
    taxonomies = []
    for _, row in df.iterrows():
      try:
        taxonomy_data = row.to_dict()
        taxonomy = Taxonomy.create_from_dict(user_id, taxonomy_data)
        taxonomies.append(taxonomy)
      except Exception as e:
        import traceback
        traceback.print_exc()  # This prints the full traceback
        from flask import current_app
        current_app.logger.error(f"Error creating taxonomy: {e}")
        continue

    return taxonomies

  @staticmethod
  def get_user_taxonomies(user_id, level=None, limit=None):
    """Get taxonomies for a user, optionally filtered by taxonomic level"""
    query = Taxonomy.query.filter_by(user_id=user_id)

    if level:
      # Filter by taxonomic level
      if level == 'species':
        query = query.filter(Taxonomy.species.isnot(None))
      elif level == 'genus':
        query = query.filter(Taxonomy.genus.isnot(None),
                             Taxonomy.species.is_(None))
      elif level == 'family':
        query = query.filter(Taxonomy.family.isnot(None),
                             Taxonomy.genus.is_(None))
      # Add more levels as needed

    if limit:
      query = query.limit(limit)

    return query.all()

  @staticmethod
  def search_taxonomies(user_id, search_term, level=None):
    """Search taxonomies by name"""
    query = Taxonomy.query.filter_by(user_id=user_id)

    # Search across all taxonomic levels
    search_filter = db.or_(
        Taxonomy.domain.ilike(f'%{search_term}%'),
        Taxonomy.phylum.ilike(f'%{search_term}%'),
        Taxonomy.class_name.ilike(f'%{search_term}%'),
        Taxonomy.order.ilike(f'%{search_term}%'),
        Taxonomy.family.ilike(f'%{search_term}%'),
        Taxonomy.genus.ilike(f'%{search_term}%'),
        Taxonomy.species.ilike(f'%{search_term}%'),
        Taxonomy.taxonomy_id.ilike(f'%{search_term}%')
    )

    query = query.filter(search_filter)

    if level:
      query = query.filter(getattr(Taxonomy, level).isnot(None))

    return query.all()


class BrackenResult(db.Model):
  """
  Bracken abundance results for taxonomies across different timepoints

  Features:
  - Links taxonomies to patients with abundance data
  - Multiple timepoints (pre, during, post-treatment)
  - Delta calculations between timepoints
  """

  __tablename__ = 'bracken_results'

  # Primary identification
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  patient_id = db.Column(db.String(50), nullable=False, index=True)
  taxonomy_id = db.Column(db.String(100), nullable=False, index=True)

  # Abundance values at different timepoints
  abundance_pre = db.Column(db.Float, nullable=True)    # .P suffix
  abundance_during = db.Column(db.Float, nullable=True)  # .E suffix
  abundance_post = db.Column(db.Float, nullable=True)   # .2.4M suffix

  # Delta calculations
  delta_during_pre = db.Column(db.Float, nullable=True)     # .E - .P
  delta_post_during = db.Column(db.Float, nullable=True)    # .2.4M - .E
  delta_post_pre = db.Column(db.Float, nullable=True)       # .2.4M - .P

  # Quality metrics
  quality_score = db.Column(db.Float, nullable=True)
  confidence = db.Column(db.Float, nullable=True)

  # Metadata
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
  updated_at = db.Column(
      db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relationships
  taxonomy = db.relationship('Taxonomy',
                             primaryjoin='and_(BrackenResult.taxonomy_id == Taxonomy.taxonomy_id, '
                             'BrackenResult.user_id == Taxonomy.user_id)',
                             foreign_keys=[taxonomy_id, user_id],
                             viewonly=True)

  def __init__(self, user_id=None, **kwargs):
    """Initialize a new BrackenResult instance"""
    super().__init__(**kwargs)
    if user_id:
      self.user_id = user_id

  def __repr__(self):
    return f'<BrackenResult {self.patient_id}-{self.taxonomy_id}>'

  def calculate_deltas(self):
    """Calculate delta values between timepoints"""
    if self.abundance_during is not None and self.abundance_pre is not None:
      self.delta_during_pre = self.abundance_during - self.abundance_pre

    if self.abundance_post is not None and self.abundance_during is not None:
      self.delta_post_during = self.abundance_post - self.abundance_during

    if self.abundance_post is not None and self.abundance_pre is not None:
      self.delta_post_pre = self.abundance_post - self.abundance_pre

  def get_abundance_at_timepoint(self, timepoint):
    """Get abundance at specific timepoint"""
    timepoint_map = {
        'pre': self.abundance_pre,
        'during': self.abundance_during,
        'post': self.abundance_post
    }
    return timepoint_map.get(timepoint)

  def get_delta_value(self, delta_type):
    """Get delta value of specific type"""
    delta_map = {
        'during_pre': self.delta_during_pre,
        'post_during': self.delta_post_during,
        'post_pre': self.delta_post_pre
    }
    return delta_map.get(delta_type)

  def to_dict(self):
    """Convert to dictionary for API responses"""
    return {
        'id': self.id,
        'patient_id': self.patient_id,
        'taxonomy_id': self.taxonomy_id,
        'abundance_pre': self.abundance_pre,
        'abundance_during': self.abundance_during,
        'abundance_post': self.abundance_post,
        'delta_during_pre': self.delta_during_pre,
        'delta_post_during': self.delta_post_during,
        'delta_post_pre': self.delta_post_pre,
        'quality_score': self.quality_score,
        'taxonomy_info': self.taxonomy.to_dict() if self.taxonomy else None
    }

  @staticmethod
  def create_from_dict(user_id, bracken_data):
    """Create bracken result from dictionary"""
    result = BrackenResult(user_id=user_id, **bracken_data)
    result.calculate_deltas()
    db.session.add(result)
    db.session.commit()
    return result

  @staticmethod
  def bulk_create_from_dataframe(user_id, df):
    """Create multiple bracken results from DataFrame"""
    results = []
    for _, row in df.iterrows():
      try:
        bracken_data = row.to_dict()
        result = BrackenResult.create_from_dict(user_id, bracken_data)
        results.append(result)
      except Exception as e:
        import traceback
        traceback.print_exc()  # This prints the full traceback
        from flask import current_app
        current_app.logger.error(f"Error creating bracken result: {e}")
        continue

    return results
