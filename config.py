# Flask Application Configuration
import os
from datetime import timedelta


class Config:
  # Basic Flask settings
  SECRET_KEY = os.environ.get('SECRET_KEY')
  WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY')

  # Database settings
  SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ENGINE_OPTIONS = {
      'pool_pre_ping': True,
      'pool_recycle': 300,
      'pool_timeout': 20,
      'max_overflow': 0
  }

  # Session settings
  PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
  SESSION_COOKIE_SECURE = os.environ.get(
      'SESSION_COOKIE_SECURE', 'False').lower() == 'true'
  SESSION_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SAMESITE = 'Lax'

  # File upload settings
  MAX_CONTENT_LENGTH = int(os.environ.get(
      'MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
  UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
  ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}

  # OAuth settings
  GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
  GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
  GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

  # Redis settings
  REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

  # Celery settings
  CELERY_BROKER_URL = os.environ.get(
      'CELERY_BROKER_URL', 'redis://localhost:6379/0')
  CELERY_RESULT_BACKEND = os.environ.get(
      'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

  # Mail settings
  MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
  MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
  MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
  MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
  MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

  # Logging settings
  LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
  LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

  # Rate limiting
  RATELIMIT_STORAGE_URL = os.environ.get(
      'RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')

  # API settings
  API_VERSION = os.environ.get('API_VERSION', 'v1')
  API_PREFIX = os.environ.get('API_PREFIX', '/api/v1')

  # Data Processing settings
  CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 1000))
  MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))
  CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 3600))

  # Security settings
  ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
  JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
  AUDIT_LOG_ENABLED = os.environ.get(
      'AUDIT_LOG_ENABLED', 'True').lower() == 'true'

  # Performance settings
  MAX_CONCURRENT_USERS = int(os.environ.get('MAX_CONCURRENT_USERS', 100))
  DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
  DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))


class DevelopmentConfig(Config):
  DEBUG = True
  TESTING = False

  # Allow default secrets for development only
  SECRET_KEY = os.environ.get(
      'SECRET_KEY') or 'dev-secret-key-change-in-production'
  WTF_CSRF_SECRET_KEY = os.environ.get(
      'WTF_CSRF_SECRET_KEY') or 'csrf-secret-key'


class ProductionConfig(Config):
  DEBUG = False
  TESTING = False

  # Require environment variables in production
  def __init__(self):
    if not self.SECRET_KEY:
      raise ValueError(
          "SECRET_KEY environment variable must be set in production")
    if not self.WTF_CSRF_SECRET_KEY:
      raise ValueError(
          "WTF_CSRF_SECRET_KEY environment variable must be set in production")
  SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
  TESTING = True
  SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
  WTF_CSRF_ENABLED = False


# Statistical Analysis Configuration
ANALYSIS_METHODS = {
    'cox': {
        'name': 'Cox Proportional Hazards',
        'description': 'Survival analysis using Cox regression model',
        'parameters': ['alpha', 'penalizer', 'step_size']
    },
    'rmst': {
        'name': 'Restricted Mean Survival Time',
        'description': 'RMST difference analysis',
        'parameters': ['tau', 'alpha', 'return_variance']
    },
    'kaplan_meier': {
        'name': 'Kaplan-Meier Estimator',
        'description': 'Non-parametric survival analysis',
        'parameters': ['alpha', 'ci_labels']
    },
    'log_rank': {
        'name': 'Log-Rank Test',
        'description': 'Statistical test comparing survival distributions',
        'parameters': ['alpha']
    }
}

# Clustering Configuration
CLUSTERING_METHODS = {
    'hierarchical': {
        'name': 'Hierarchical Clustering',
        'parameters': ['linkage', 'metric', 'n_clusters']
    },
    'kmeans': {
        'name': 'K-Means Clustering',
        'parameters': ['n_clusters', 'random_state', 'max_iter']
    },
    'dbscan': {
        'name': 'DBSCAN',
        'parameters': ['eps', 'min_samples', 'metric']
    }
}

# Data Quality Thresholds
DATA_QUALITY_THRESHOLDS = {
    'missing_data_threshold': 0.3,  # 30% missing data threshold
    'outlier_std_threshold': 3,     # 3 standard deviations for outlier detection
    'correlation_threshold': 0.8,   # High correlation threshold
    'variance_threshold': 0.01      # Low variance threshold
}

# User Roles and Permissions
USER_ROLES = {
    'admin': {
        'permissions': ['read', 'write', 'delete', 'admin', 'manage_users'],
        'description': 'Full system access'
    },
    'researcher': {
        'permissions': ['read', 'write', 'share'],
        'description': 'Can create and share analyses'
    },
    'analyst': {
        'permissions': ['read', 'write'],
        'description': 'Can perform analyses'
    },
    'viewer': {
        'permissions': ['read'],
        'description': 'Read-only access'
    }
}

# column_group
demographics = [
    'age', 'gender', 'race', 'ethnicity',
    'weight_kg', 'height_m', 'bmi', 'smoking', 'smoking_status'
]

# column_group
disease_characteristics = [
    'igg', 'iga', 'biclonal', 'lightchain', 'igh_rearrangement',
    'hr_mutations', 'ultrahr_mutations', 'imwg_hr', 'functional_hr',
    'iss', 'riss', 'beta2microglobulin', 'creatinine', 'albumin'
]

# column_group
fish_indicators = [
    '3_monosomy', '3_gain', '5_gain', '7_gain', '9_monosomy', '9_gain',
    '11_monosomy', '11_gain', '13_monosomy', '15_gain', '17_monosomy',
    '19_gain', '21_gain', 'del_13q', 't_11_14', 't_4_14', 't_14_16',
    't_14_20',  '1q_plus', 'del_1p32', 'del_17p', '6q21', 't_12_22'
]

# column_group
comorbidities = [
    'es', 'esnoninfectiousfever', 'esnoninfectious_diarhhea', 'esrash'
]

# column_group
treatment_and_transplantation = [
    'induction_therapy', 'melphalanmgperm2', 'first_transplant_date',
    'date_engraftment', 'last_date_of_contact', 'monthsfirst_transplant',
    'secona_transplant_date', 'monthssecona_transplantrk',
    'rk_updated_relapse_date', 'relapsemonthsfirst_transplant',
    'relapsemonthssecona_transplant', 'duration_pfs', 'pfs_status',
    'rk_updated_death_date', 'deathmonthsfirst_transplant',
    'deathmonthssecona_transplant', 'duration_survival', 'death_status'
]

# column_group
laboratory_values = [
    'beta2microglobulin', 'creatinine', 'albumin', 'ldh', 'hemoglobin',
    'platelet_count', 'neutrophil_count', 'lymphocyte_count'
]

# column_group
genomic_markers = [
    'tp53_mutation', 'rb1_deletion', 'myc_rearrangement',
    'cyclin_d1', 'cyclin_d2', 'cyclin_d3', 'maf_rearrangement'
]

# Bracken Time Points Configuration
BRACKEN_TIME_POINTS = {
    'pre': {
        'suffix': '.P',
        'description': 'Pre-treatment sample',
        'timepoint': 'baseline'
    },
    'during': {
        'suffix': '.E',
        'description': 'Early treatment sample (2 months)',
        'timepoint': '2_months'
    },
    'post': {
        'suffix': '.2.4M',
        'description': 'Post-treatment sample (24 months)',
        'timepoint': '24_months'
    }
}

# Data Processing Configuration
DATA_PROCESSING_CONFIG = {
    'missing_value_strategies': {
        'numerical': ['mean', 'median', 'mode', 'interpolation', 'knn'],
        'categorical': ['mode', 'constant', 'unknown']
    },
    'outlier_detection_methods': ['iqr', 'zscore', 'isolation_forest', 'local_outlier_factor'],
    'normalization_methods': ['standardization', 'min_max', 'robust', 'quantile'],
    'feature_selection_methods': ['univariate', 'recursive', 'lasso', 'random_forest']
}

# Visualization Configuration
VISUALIZATION_CONFIG = {
    'color_palettes': {
        'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        'colorblind_friendly': ['#0173b2', '#de8f05', '#029e73', '#cc78bc', '#ca9161'],
        'grayscale': ['#000000', '#444444', '#888888', '#bbbbbb', '#eeeeee']
    },
    'plot_dimensions': {
        'default_width': 800,
        'default_height': 600,
        'thumbnail_width': 200,
        'thumbnail_height': 150
    }
}

# column_group
antiviral = ['Acyclovir', 'valACYclovir']

# column_group
antibiotics = [
    'ciprofloxin', 'ciprofloxin_eng', 'levofloxin', 'levofloxin_eng',
    'moxifloxin', 'moxifloxin_eng', 'amoxicillin', 'amoxicillin_eng',
    'ampicillin', 'ampicillin_eng', 'cefipine', 'cefipine_eng',
    'cefazolin', 'cefazolin_eng', 'azithromycin', 'azithromycin_eng',
    'trimethoprim_sulfamethoxazole', 'trimethoprim_sulfamethoxazole_eng',
    'clindamycin', 'clindamycin_eng', 'metronidazole', 'metronidazole_eng',
    'piperacilin_tazobactam', 'piperacilin_tazobactam_eng',
    'vancomycin_iv', 'vancomycin_iv_eng', 'vancomycin_po', 'vancomycin_po_eng'
]

# column_group
antifungal = ['fluconazole', 'fluconazole_eng']

# identification_fields
in_patients_table = ['age', 'gender', 'race', 'ethnicity']
# identification_fields
in_taxonomy_table = ['taxonomy', 'domain', 'phylum']

# field_names
duration_field_in_patients_table = 'Duration_PFS'
# field_names
event_field_in_patients_table = 'PFS_Status'

# field_names
# duration_field_in_patients_table = 'Duration_PFSDuration_Survival'

# column_names_mapping
patients_table_columns_name = [
    'patient_id', 'age', 'gender', 'race', 'ethnicity',
    'weight_kg', 'height_m', 'bmi', 'smoking', 'smoking_status',
    'igg', 'iga', 'biclonal', 'lightchain', 'igh_rearrangement',
    '3_monosomy', '3_gain', '5_gain', '7_gain', '9_monosomy', '9_gain',
    '11_monosomy', '11_gain', '13_monosomy', '15_gain', '17_monosomy',
    '19_gain', '21_gain', 'del_13q', 't_11_14', 't_4_14', 't_14_16',
    't_14_20', '1q_plus', 'del_1p32', 'del_17p', '6q21', 't_12_22',
    'hr_mutations', 'ultrahr_mutations', 'imwg_hr', 'functional_hr',
    'iss', 'riss', 'beta2microglobulin', 'creatinine', 'albumin',
    'induction_therapy', 'melphalanmgperm2', 'first_transplant_date',
    'date_engraftment', 'es', 'esnoninfectiousfever',
    'esnoninfectious_diarhhea', 'esrash', 'last_date_of_contact',
    'monthsfirst_transplant', 'secona_transplant_date',
    'monthssecona_transplantrk', 'rk_updated_relapse_date',
    'relapsemonthsfirst_transplant', 'relapsemonthssecona_transplant',
    'duration_pfs', 'pfs_status', 'rk_updated_death_date',
    'deathmonthsfirst_transplant', 'deathmonthssecona_transplant',
    'duration_survival', 'death_status',
    'ciprofloxin', 'cipropfloxin_eng', 'levofloxin', 'levofloxin_eng',
    'moxifloxin', 'moxifloxin_eng', 'amoxicillin', 'amoxicillin_eng',
    'ampicillin', 'ampicillin_eng', 'cefipine', 'cefipine_eng',
    'cefazolin', 'cefazolin_eng', 'azithromycin', 'azithromycin_eng',
    'trimethoprim_sulfamethoxazole', 'trimethoprim_sulfamethoxazole_eng',
    'clindamycin', 'clindamycin_eng', 'metronidazole', 'metronidazole_eng',
    'piperacilin_tazobactam', 'piperacilin_tazobactam_eng',
    'vancomycin_iv', 'vancomycin_iv_eng', 'vancomycin_po', 'vancomycin_po_eng',
    'fluconazole', 'fluconazole_eng',
    'start_date', 'end_date', 'start_dateeng', 'end_dateeng'
]

patients_table_identificatos = {'age', 'gender', 'race'}

taxonomy_table_columns_name = [
    'asv', 'taxonomy', 'domain', 'phylum', 'class',
    'order', 'family', 'genus', 'species'
]
taxonomy_table_identificatos = {'taxonomy', 'domain'}


# Advanced Statistical Configuration
SURVIVAL_ANALYSIS_CONFIG = {
    'default_confidence_level': 0.95,
    'default_alpha': 0.05,
    'rmst_tau_options': [12, 24, 36, 60],  # months
    'cox_penalizer_range': [0.01, 0.1, 1.0],
    'bootstrap_iterations': 1000
}

# Microbiome Analysis Configuration
MICROBIOME_CONFIG = {
    'alpha_diversity_metrics': ['shannon', 'simpson', 'chao1', 'observed_otus'],
    'beta_diversity_metrics': ['bray_curtis', 'jaccard', 'weighted_unifrac', 'unweighted_unifrac'],
    'differential_abundance_methods': ['deseq2', 'edger', 'ancom', 'aldex2'],
    'normalization_methods': ['tss', 'css', 'tmm', 'rle'],
    'minimum_prevalence': 0.1,  # 10% prevalence threshold
    'minimum_abundance': 0.001  # 0.1% abundance threshold
}

# File Processing Configuration
FILE_PROCESSING_CONFIG = {
    'excel_sheet_names': {
        'patients': ['patients', 'patient_data', 'clinical_data'],
        'taxonomy': ['taxonomy', 'taxa', 'taxonomies'],
        'bracken': ['bracken', 'abundance', 'counts']
    },
    'date_formats': ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'],
    'encoding_options': ['utf-8', 'latin-1', 'cp1252'],
    'delimiter_options': [',', ';', '\t', '|']
}

# Validation Rules Configuration
VALIDATION_RULES = {
    'patient_id': {
        'pattern': r'^[A-Za-z0-9_-]+$',
        'min_length': 3,
        'max_length': 50
    },
    'age': {
        'min_value': 0,
        'max_value': 120
    },
    'duration_pfs': {
        'min_value': 0,
        'max_value': 3650  # 10 years in days
    },
    'laboratory_values': {
        'creatinine': {'min': 0.1, 'max': 20.0},  # mg/dL
        'albumin': {'min': 1.0, 'max': 6.0},  # g/dL
        'beta2microglobulin': {'min': 0.5, 'max': 50.0}  # mg/L
    }
}

# Export Configuration
EXPORT_CONFIG = {
    'report_formats': ['pdf', 'html', 'docx'],
    'data_formats': ['csv', 'xlsx', 'json', 'parquet'],
    'figure_formats': ['png', 'svg', 'pdf', 'jpg'],
    'figure_dpi': 300,
    'max_export_rows': 100000
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    'email_templates': {
        'analysis_complete': 'analysis_complete.html',
        'error_notification': 'error_notification.html',
        'shared_result': 'shared_result.html'
    },
    'notification_types': ['email', 'in_app', 'webhook'],
    'retry_attempts': 3,
    'retry_delay': 300  # 5 minutes
}

# Cache Configuration
CACHE_CONFIG = {
    'analysis_results_ttl': 86400,  # 24 hours
    'data_preview_ttl': 3600,  # 1 hour
    'user_preferences_ttl': 604800,  # 1 week
    'statistical_models_ttl': 43200  # 12 hours
}

# Audit Trail Configuration
AUDIT_CONFIG = {
    'tracked_events': [
        'user_login', 'user_logout', 'data_upload', 'data_delete',
        'analysis_run', 'result_export', 'settings_change', 'user_created'
    ],
    'retention_days': 2555,  # 7 years for compliance
    'sensitive_fields': ['password', 'secret_key', 'token'],
    'log_format': 'json'
}

# Statistical Power Analysis Configuration
POWER_ANALYSIS_CONFIG = {
    'default_power': 0.80,
    'default_alpha': 0.05,
    'effect_sizes': {
        'small': 0.2,
        'medium': 0.5,
        'large': 0.8
    },
    'sample_size_methods': ['cox_regression', 'log_rank', 'rmst'],
    'power_calculation_methods': ['analytic', 'simulation', 'bootstrap'],
    'minimum_events_per_variable': 10,
    'recommended_events_per_variable': 15
}

# Model Validation Configuration
MODEL_VALIDATION_CONFIG = {
    'cross_validation': {
        'method': 'time_aware_cv',
        'folds': 5,
        'stratify_by': 'event_status'
    },
    'bootstrap': {
        'iterations': 1000,
        'confidence_level': 0.95,
        'bias_correction': True
    },
    'performance_metrics': {
        'discrimination': ['c_index', 'auc_roc', 'auc_pr'],
        'calibration': ['brier_score', 'calibration_slope', 'calibration_intercept'],
        'clinical_utility': ['decision_curve_analysis', 'net_benefit'],
        'reclassification': ['idi', 'nri', 'categorical_nri']
    },
    'assumption_tests': {
        'proportional_hazards': ['schoenfeld_test', 'scaled_schoenfeld'],
        'linearity': ['martingale_residuals', 'deviance_residuals'],
        'independence': ['dfbeta', 'influence_measures']
    }
}

# Publication Quality Standards
PUBLICATION_CONFIG = {
    'figure_standards': {
        'dpi': 300,
        'formats': ['pdf', 'svg', 'png'],
        'color_scheme': 'colorblind_friendly',
        'font_family': 'Arial',
        'font_sizes': {
            'title': 14,
            'axis_labels': 12,
            'tick_labels': 10,
            'legend': 10
        }
    },
    'table_standards': {
        'decimal_places': 3,
        'p_value_threshold': 0.001,
        'confidence_intervals': True,
        'effect_size_reporting': True
    },
    'reproducibility': {
        'random_seed': 42,
        'software_versions': True,
        'parameter_logging': True,
        'code_generation': True
    },
    'reporting_guidelines': {
        'strobe': True,
        'consort': True,
        'spirit': True,
        'tripod': True
    }
}

# Advanced Grouping Strategy Configuration
GROUPING_STRATEGIES = {
    'none': {
        'name': 'Standard Analysis',
        'description': 'Analyze all variables together without grouping',
        'groups': None,
        'method': 'standard_multivariate'
    },
    'fish_indicators': {
        'name': 'FISH Indicators Grouping',
        'description': 'Cytogenetic abnormalities grouped by biological significance',
        'groups': {
            'chromosome_gains': ['3_gain', '5_gain', '7_gain', '9_gain', '11_gain', '15_gain', '19_gain', '21_gain', '1q_plus'],
            'chromosome_losses': ['3_monosomy', '9_monosomy', '11_monosomy', '13_monosomy', '17_monosomy', 'del_13q', 'del_1p32', 'del_17p'],
            'high_risk_translocations': ['t_11_14', 't_4_14', 't_14_16', 't_14_20'],
            'other_abnormalities': ['6q21', 't_12_22'],
            # Can overlap for complex analysis
            'complex_abnormalities': ['1q_plus', 'del_17p', 'del_1p32']
        },
        'method': 'hierarchical_grouping'
    },
    'disease_characteristics': {
        'name': 'Disease Characteristics Grouping',
        'description': 'Clinical parameters grouped by pathophysiological systems',
        'groups': {
            'immunoglobulin_profile': ['igg', 'iga', 'biclonal', 'lightchain'],
            'disease_staging': ['iss', 'riss', 'beta2microglobulin', 'albumin', 'creatinine'],
            'molecular_risk': ['igh_rearrangement', 'hr_mutations', 'ultrahr_mutations'],
            'functional_assessment': ['imwg_hr', 'functional_hr']
        },
        'method': 'pathway_analysis'
    },
    'demographics': {
        'name': 'Demographics Grouping',
        'description': 'Patient characteristics grouped by risk stratification',
        'groups': {
            # Will be categorized as <65, 65-75, >75
            'age_stratification': ['age'],
            'physical_characteristics': ['weight_kg', 'height_m', 'bmi'],
            'lifestyle_factors': ['smoking', 'smoking_status'],
            'population_factors': ['gender', 'race', 'ethnicity']
        },
        'method': 'stratified_analysis'
    },
    'genomic_markers': {
        'name': 'Genomic Markers Grouping',
        'description': 'Molecular markers grouped by functional pathways',
        'groups': {
            'tumor_suppressor_pathway': ['tp53_mutation', 'rb1_deletion'],
            'oncogene_pathway': ['myc_rearrangement'],
            'cell_cycle_regulation': ['cyclin_d1', 'cyclin_d2', 'cyclin_d3'],
            'transcription_factors': ['maf_rearrangement']
        },
        'method': 'pathway_analysis'
    },
    'laboratory_values': {
        'name': 'Laboratory Values Grouping',
        'description': 'Lab parameters grouped by organ system function',
        'groups': {
            'kidney_function': ['creatinine', 'beta2microglobulin'],
            'liver_function': ['albumin', 'ldh'],
            'hematologic_parameters': ['hemoglobin', 'platelet_count', 'neutrophil_count', 'lymphocyte_count'],
            'inflammatory_markers': ['ldh', 'beta2microglobulin']  # Can overlap
        },
        'method': 'organ_system_analysis'
    },
    'treatment_response': {
        'name': 'Treatment Response Grouping',
        'description': 'Treatment variables grouped by response patterns',
        'groups': {
            'induction_therapy': ['induction_therapy'],
            'transplant_factors': ['melphalanmgperm2', 'first_transplant_date', 'date_engraftment', 'monthsfirst_transplant'],
            'secondary_transplant': ['secona_transplant_date', 'monthssecona_transplantrk'],
            'outcome_measures': ['duration_pfs', 'pfs_status', 'duration_survival', 'death_status'],
            'relapse_patterns': ['rk_updated_relapse_date', 'relapsemonthsfirst_transplant', 'relapsemonthssecona_transplant'],
            'survival_metrics': ['rk_updated_death_date', 'deathmonthsfirst_transplant', 'deathmonthssecona_transplant']
        },
        'method': 'temporal_analysis'
    }
}

# Grouping Strategy Analysis Methods
GROUPING_ANALYSIS_METHODS = {
    'standard_multivariate': {
        'description': 'Standard penalized regression on all variables',
        'models': ['cox_lasso', 'cox_elastic_net', 'random_survival_forest'],
        'validation': 'nested_cv'
    },
    'hierarchical_grouping': {
        'description': 'Hierarchical analysis with group-level and within-group effects',
        'models': ['cox_frailty', 'group_lasso', 'hierarchical_cox'],
        'validation': 'group_cv'
    },
    'pathway_analysis': {
        'description': 'Pathway-based analysis with biological constraints',
        'models': ['pathway_lasso', 'group_bridge', 'sparse_group_lasso'],
        'validation': 'pathway_cv'
    },
    'stratified_analysis': {
        'description': 'Stratified analysis by subgroups',
        'models': ['stratified_cox', 'interaction_cox', 'subgroup_analysis'],
        'validation': 'stratified_cv'
    },
    'organ_system_analysis': {
        'description': 'Organ system-based functional analysis',
        'models': ['functional_cox', 'system_lasso', 'composite_scoring'],
        'validation': 'system_cv'
    },
    'temporal_analysis': {
        'description': 'Time-dependent analysis of treatment effects',
        'models': ['time_varying_cox', 'landmark_analysis', 'joint_modeling'],
        'validation': 'temporal_cv'
    }
}

# Group Analysis Reporting Configuration
GROUP_REPORTING_CONFIG = {
    'report_types': {
        'individual_group': {
            'sections': ['group_composition', 'descriptive_stats', 'univariate_analysis',
                         'multivariate_analysis', 'survival_curves', 'forest_plots', 'interpretation'],
            'format': 'detailed_scientific'
        },
        'cross_group_comparison': {
            'sections': ['group_summaries', 'effect_size_comparison', 'significance_testing',
                         'model_performance', 'clinical_ranking', 'recommendations'],
            'format': 'comparative_analysis'
        },
        'integrated_report': {
            'sections': ['executive_summary', 'methodology', 'individual_results',
                         'comparative_analysis', 'clinical_implications', 'limitations', 'conclusions'],
            'format': 'comprehensive_scientific'
        },
        'executive_summary': {
            'sections': ['key_findings', 'clinical_recommendations', 'risk_stratification', 'actionable_insights'],
            'format': 'clinical_decision_support'
        }
    },
    'visualization_types': {
        'group_specific': ['survival_curves', 'forest_plots', 'variable_importance', 'correlation_heatmaps'],
        'cross_group': ['comparison_plots', 'effect_size_plots', 'model_performance_comparison', 'clinical_impact_ranking'],
        'integrated': ['comprehensive_forest_plot', 'risk_stratification_plot', 'decision_tree', 'clinical_algorithm']
    }
}
