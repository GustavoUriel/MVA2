# MVA2 Project Guidelines and Standards

This document contains general considerations and guidelines that should always be followed when working on the MVA2 project.

## Development Environment Guidelines

### Virtual Environment
- **ALWAYS** use the project's virtual environment when installing dependencies or running commands
- Virtual environment is located at `.venv` in the project root
- Activate using: `.\.venv\Scripts\Activate.ps1` (Windows PowerShell) or `source .venv/bin/activate` (Unix/Linux)
- Never install packages globally - all dependencies must be managed through the virtual environment
- Update `requirements.txt` when adding new dependencies

### Database Column Naming Convention
- **ALWAYS** use lowercase for database column names
- Use snake_case for multi-word column names (e.g., `taxonomy_id`, `patient_id`)
- Be consistent with naming conventions across all tables
- When importing data, normalize column names to lowercase before processing

### Work Documentation
- **ALWAYS** append details of significant work to `reports_2.md`
- Include:
  - Summary of changes made
  - Files modified
  - Database migrations performed
  - Any breaking changes or considerations
  - Testing performed
- Use clear, descriptive commit messages
- Document any configuration changes or new requirements

## Data Import Guidelines

### Column Mapping
- Implement fuzzy matching for column names to handle variations in input data
- Use the `app/utils/data_mapping.py` utilities for consistent column mapping
- Handle common variations in column names (case differences, extra spaces, etc.)
- Always validate mapped data before database insertion

### Taxonomy Data Structure
The standard taxonomy table structure should include these columns (all lowercase):
- `taxonomy_id` - Unique identifier for the taxonomy entry
- `taxonomy` - Full taxonomic name/string
- `domain` - Taxonomic domain
- `phylum` - Taxonomic phylum  
- `class` - Taxonomic class (stored as `class_name` in model due to Python keyword)
- `order` - Taxonomic order
- `family` - Taxonomic family
- `genus` - Taxonomic genus
- `species` - Taxonomic species

### Patient Data Structure
Follow the standard patient table columns as defined in `config.py` under `patients_table_columns_name`.

## Code Quality Standards

### Error Handling
- Implement comprehensive error handling for data import processes
- Log errors with sufficient context for debugging
- Provide meaningful error messages to users
- Use try-catch blocks around database operations

### Testing
- Test data import functionality with sample datasets
- Verify fuzzy matching works with various column name formats
- Test database migrations on development environment before production
- Validate data integrity after imports

### Security
- Never commit sensitive configuration data
- Use environment variables for secrets
- Validate all user inputs
- Implement proper access controls

## File Organization

### Configuration Files
- Main configuration: `config.py`
- Project guidelines: `project_guidelines.md` (this file)
- Requirements: `requirements.txt`

### Database Management
- Models: `app/models/`
- Migrations: `migrations/versions/`
- Use Flask-Migrate for all database schema changes

### Data Processing
- Import utilities: `app/utils/data_mapping.py`
- Upload handling: `app/api/uploads.py`
- Data validation: `app/utils/validators.py`

## Deployment Considerations

### Database Migrations
- Always create migrations for schema changes
- Test migrations on development database first
- Back up production database before applying migrations
- Document migration steps in work reports

### Environment Setup
- Ensure virtual environment is properly configured in deployment
- Install all requirements from `requirements.txt`
- Set appropriate environment variables
- Configure logging for production environment

## Maintenance Guidelines

### Regular Tasks
- Keep requirements.txt updated
- Review and clean up temporary files
- Monitor log files for errors
- Update documentation when adding new features

### Code Review
- Follow established coding patterns
- Maintain consistency with existing codebase
- Document complex logic
- Ensure proper error handling

---

**Remember**: These guidelines should be consulted before making any significant changes to the project. When in doubt, refer to this document and maintain consistency with existing patterns.
