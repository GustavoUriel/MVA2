# MVA2 - Multiple Myeloma Multivariate Analysis Platform

A comprehensive web-based platform for biomedical research focusing on multiple myeloma analysis with advanced statistical methods and microbiome data processing capabilities.

## 🚀 Features

### 🔐 Authentication & Security
- **Google OAuth 2.0 Integration**: Secure authentication with Google accounts
- **Role-based Access Control**: Admin, Researcher, Analyst, and Viewer roles
- **HIPAA Compliance**: Secure handling of patient health information
- **Session Management**: Secure session handling with CSRF protection
- **Data Encryption**: Encrypted sensitive data storage

### 📊 Patient Data Management
- **Clinical Data Storage**: Comprehensive patient demographics and clinical information
- **FISH Analysis**: Fluorescence in situ hybridization data management
- **Laboratory Values**: Complete laboratory test results tracking
- **Treatment Data**: Treatment regimens and response tracking
- **Survival Analysis**: Overall survival and progression-free survival data

### 🧬 Microbiome Analysis
- **Taxonomic Classifications**: Full taxonomic hierarchy management
- **Bracken Results**: Abundance data across multiple timepoints
- **Delta Calculations**: Automated calculation of abundance changes
- **Quality Metrics**: Data quality assessment and filtering

### 📈 Advanced Statistical Analysis
- **Cox Proportional Hazards Regression**: Survival analysis with hazard ratios
- **Kaplan-Meier Estimator**: Survival curve generation and comparison
- **Restricted Mean Survival Time (RMST)**: Advanced survival metrics
- **Non-parametric Tests**: Wilcoxon, Mann-Whitney, Kruskal-Wallis
- **Correlation Analysis**: Pearson, Spearman, and Kendall correlations
- **Differential Abundance Analysis**: Microbiome comparative analysis

### 📊 Data Visualization
- **Interactive Charts**: Survival curves, heatmaps, volcano plots
- **Publication-ready Figures**: High-quality plots for research papers
- **Dashboard Analytics**: Real-time data overview and statistics
- **Custom Visualizations**: Configurable chart types and parameters

### 🔄 Data Processing
- **Batch Upload**: Bulk data import from CSV/Excel files
- **Data Validation**: Comprehensive input validation and error checking
- **Export Capabilities**: CSV, Excel, and JSON export formats
- **Report Generation**: Automated publication-ready reports

## 🏗️ Technical Architecture

### Backend Framework
- **Flask 2.3.3**: Modern Python web framework
- **SQLAlchemy 2.0.21**: Advanced ORM with PostgreSQL support
- **Flask-Login**: User session management
- **Flask-RESTX**: RESTful API development
- **Alembic**: Database migration management

### Database Design
- **PostgreSQL**: Production database (SQLite for development)
- **Redis**: Caching and session storage
- **User Data Isolation**: Complete separation of user data
- **Optimized Queries**: Efficient database operations

### Frontend Technologies
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Interactive data visualizations
- **HTMX**: Dynamic content updates
- **Custom CSS**: Professional styling and themes

### Security Features
- **HTTPS Enforcement**: Secure communication
- **Rate Limiting**: API protection against abuse
- **Input Sanitization**: XSS and injection prevention
- **Audit Trails**: Complete user action logging
- **Data Anonymization**: Privacy protection features

### Scientific Computing
- **SciPy/NumPy**: Statistical computations
- **Pandas**: Data manipulation and analysis
- **Lifelines**: Survival analysis library
- **Scikit-learn**: Machine learning algorithms
- **Matplotlib/Seaborn**: Plot generation

## 🚀 Installation & Setup

### Prerequisites
```bash
# Python 3.9+
python --version

# PostgreSQL (optional, SQLite works for development)
psql --version

# Redis (optional, for caching)
redis-server --version
```

### Environment Setup
```bash
# Clone repository
git clone https://github.com/yourusername/MVA2.git
cd MVA2

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
1. **Environment Variables**: Create `.env` file:
```env
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
DATABASE_URL=postgresql://user:password@localhost/mva2
REDIS_URL=redis://localhost:6379/0
```

2. **Google OAuth Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs

### Database Initialization
```bash
# Initialize database
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade

# Create admin user
flask create-admin --email admin@example.com --name "Admin User"
```

### Running the Application
```bash
# Development server
python run.py

# Production (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

## 📱 Usage Guide

### Getting Started
1. **Sign In**: Use Google OAuth to authenticate
2. **Upload Data**: Navigate to "Upload Data" and import patient/microbiome files
3. **Verify Data**: Review imported data for accuracy
4. **Create Analysis**: Set up statistical analysis workflows
5. **View Results**: Examine analysis results and visualizations
6. **Generate Reports**: Export publication-ready reports

### Data Upload Formats

#### Patient Data (CSV/Excel)
```csv
patient_id,age,sex,race,diagnosis_date,stage,survival_months,survival_status
MM001,65,M,White,2020-01-15,IIIA,24.5,0
MM002,58,F,Black,2019-08-22,IIA,18.2,1
```

#### Microbiome Data (CSV)
```csv
taxonomy_id,patient_id,abundance_pre,abundance_during,abundance_post
Bacteroides_fragilis,MM001,0.15,0.12,0.08
Lactobacillus_acidophilus,MM001,0.03,0.05,0.07
```

### Analysis Workflows

#### Survival Analysis
1. Select patients and survival variables
2. Choose analysis type (Cox regression, Kaplan-Meier, RMST)
3. Configure parameters (confidence intervals, time units)
4. Execute analysis and review results

#### Microbiome Analysis
1. Upload taxonomic abundance data
2. Select timepoints for comparison
3. Configure statistical tests
4. Generate differential abundance plots

## 🔧 API Documentation

### Authentication Endpoints
```
POST /api/v1/auth/google - Google OAuth authentication
POST /api/v1/auth/logout - User logout
GET  /api/v1/auth/status - Authentication status
```

### Patient Data API
```
GET    /api/v1/patients - List patients
POST   /api/v1/patients - Create patient
GET    /api/v1/patients/{id} - Get patient details
PUT    /api/v1/patients/{id} - Update patient
DELETE /api/v1/patients/{id} - Delete patient
```

### Analysis API
```
GET  /api/v1/analysis - List analyses
POST /api/v1/analysis - Create analysis
GET  /api/v1/analysis/{id} - Get analysis results
```

### Data Export API
```
GET /api/v1/patients/export - Export patient data
GET /api/v1/analysis/{id}/export - Export analysis results
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app tests/

# Run specific test file
python -m pytest tests/test_models.py
```

### API Testing
```bash
# Test API endpoints
python -m pytest tests/test_api.py

# Load testing (optional)
locust -f tests/locustfile.py
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
# Use provided Dockerfile
docker build -t mva2 .
docker run -p 8000:8000 mva2
```

### Production Considerations
- **Database**: Use PostgreSQL for production
- **Caching**: Configure Redis for session storage
- **Security**: Enable HTTPS with SSL certificates
- **Monitoring**: Set up application monitoring (Sentry, etc.)
- **Backup**: Regular database backups
- **Scaling**: Use load balancers for high availability

## 📊 Data Models

### User Model
- Authentication and profile information
- Role-based permissions
- Saved analyses and views
- File management

### Patient Model
- Demographics and clinical data
- FISH analysis results
- Laboratory values
- Treatment information
- Survival outcomes

### Taxonomy Model
- Taxonomic classifications
- Abundance statistics
- Functional annotations
- Quality metrics

### Analysis Model
- Analysis configurations
- Statistical results
- Visualization data
- Execution status

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards
- **PEP 8**: Python code styling
- **Type Hints**: Use type annotations
- **Docstrings**: Document all functions
- **Testing**: Maintain test coverage >80%

### Issue Reporting
- Use GitHub issues for bug reports
- Include detailed reproduction steps
- Provide system information

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [API Reference](docs/api-reference.md)

### Community
- **Issues**: [GitHub Issues](https://github.com/yourusername/MVA2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/MVA2/discussions)
- **Email**: support@mva2platform.com

## 🙏 Acknowledgments

- Flask community for excellent documentation
- SciPy ecosystem for statistical computing tools
- Bootstrap team for responsive UI framework
- Google for OAuth integration
- All contributors and users of the platform

## 📈 Roadmap

### Upcoming Features
- [ ] Machine learning integration
- [ ] Advanced microbiome diversity metrics
- [ ] Collaborative analysis sharing
- [ ] Mobile application
- [ ] Integration with public databases
- [ ] Advanced visualization options

### Version History
- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Enhanced microbiome analysis
- **v1.2.0**: Advanced statistical methods
- **v2.0.0**: Complete UI redesign and API improvements

---

**MVA2 Platform** - Advancing biomedical research through comprehensive data analysis and visualization tools.
