"""
Taxonomy data API endpoints for MVA2 application

Handles taxonomy data CRUD operations, default data loading, and data management.
"""

import os
import pandas as pd
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_login import login_required, current_user

from app.models.taxonomy import Taxonomy, BrackenResult
from app import db
from app.utils.logging_utils import (
    user_logger, log_step, log_database_operation, log_file_operation,
    log_validation, log_api_request, log_api_response, log_error,
    log_warning, log_critical, log_function
)

taxonomy_ns = Namespace('taxonomy', description='Taxonomy data operations')

# Response models
taxonomy_model = taxonomy_ns.model('Taxonomy', {
    'id': fields.Integer(description='Database ID'),
    'taxonomy_id': fields.String(description='Taxonomy identifier'),
    'asv': fields.String(description='ASV identifier'),
    'domain': fields.String(description='Domain classification'),
    'phylum': fields.String(description='Phylum classification'),
    'class': fields.String(description='Class classification'),
    'order': fields.String(description='Order classification'),
    'family': fields.String(description='Family classification'),
    'genus': fields.String(description='Genus classification'),
    'species': fields.String(description='Species classification'),
    'full_taxonomy': fields.String(description='Full taxonomic lineage'),
    'total_abundance': fields.Float(description='Total abundance'),
    'mean_abundance': fields.Float(description='Mean abundance'),
    'prevalence': fields.Float(description='Prevalence across samples'),
    'created_at': fields.DateTime(description='Record creation date')
})

taxonomy_list_model = taxonomy_ns.model('TaxonomyList', {
    'taxonomies': fields.List(fields.Nested(taxonomy_model)),
    'total_count': fields.Integer(description='Total number of taxonomies'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Records per page'),
    'pages': fields.Integer(description='Total pages')
})


@taxonomy_ns.route('/')
class TaxonomyList(Resource):
  """Taxonomy list endpoint"""

  @taxonomy_ns.doc('list_taxonomies')
  @taxonomy_ns.marshal_with(taxonomy_list_model)
  @taxonomy_ns.param('page', 'Page number', type=int, default=1)
  @taxonomy_ns.param('per_page', 'Records per page', type=int, default=50)
  @taxonomy_ns.param('search', 'Search term', type=str)
  @taxonomy_ns.param('level', 'Taxonomic level filter', type=str)
  @login_required
  @log_function('taxonomy')
  def get(self):
    """List taxonomies for current user"""
    log_api_request('GET', '/taxonomy', 'taxonomy',
                    user_id=current_user.id, user_email=current_user.email)

    try:
      log_step("Parse request parameters", "START", 'taxonomy')
      page = request.args.get('page', 1, type=int)
      per_page = min(request.args.get('per_page', 50, type=int), 200)
      search = request.args.get('search', '')
      level = request.args.get('level', '')
      # Sorting and filtering
      sort_by = request.args.get('sort_by', 'id')
      sort_dir = request.args.get('sort_dir', 'asc')
      # Per-column filters: filter_<column>=value
      filters = {}
      for col in ['taxonomy_id', 'asv', 'domain', 'phylum', 'class', 'order', 'family', 'genus', 'species']:
        v = request.args.get(f'filter_{col}')
        if v:
          filters[col] = v

      log_step("Parse request parameters", "SUCCESS", 'taxonomy',
               page=page, per_page=per_page, search=search, level=level,
               sort_by=sort_by, sort_dir=sort_dir, filters=list(filters.keys()))

      log_step("Build base query", "START", 'taxonomy')
      log_database_operation("SELECT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="filter_by_user")
      query = Taxonomy.query.filter_by(user_id=current_user.id)

      # Apply per-column filters
      col_map = {
          'taxonomy_id': Taxonomy.taxonomy_id,
          'asv': Taxonomy.asv,
          'domain': Taxonomy.domain,
          'phylum': Taxonomy.phylum,
          'class': Taxonomy.class_name,
          'order': Taxonomy.order,
          'family': Taxonomy.family,
          'genus': Taxonomy.genus,
          'species': Taxonomy.species
      }
      for col, val in filters.items():
        if col in col_map:
          query = query.filter(col_map[col].ilike(f"%{val}%"))

      log_step("Build base query", "SUCCESS", 'taxonomy')
      # Apply search filter (global across main text columns)
      if search:
        log_step("Apply search filter", "START", 'taxonomy', search_term=search)
        query = query.filter(
            db.or_(
                Taxonomy.taxonomy_id.ilike(f'%{search}%'),
                Taxonomy.domain.ilike(f'%{search}%'),
                Taxonomy.phylum.ilike(f'%{search}%'),
                Taxonomy.class_name.ilike(f'%{search}%'),
                Taxonomy.order.ilike(f'%{search}%'),
                Taxonomy.family.ilike(f'%{search}%'),
                Taxonomy.genus.ilike(f'%{search}%'),
                Taxonomy.species.ilike(f'%{search}%')
            )
        )
        log_step("Apply search filter", "SUCCESS", 'taxonomy')

      # Apply level filter
      if level:
        log_step("Apply level filter", "START", 'taxonomy', level=level)
        if level == 'species':
          query = query.filter(Taxonomy.species.isnot(None))
        elif level == 'genus':
          query = query.filter(Taxonomy.genus.isnot(None))
        elif level == 'family':
          query = query.filter(Taxonomy.family.isnot(None))
        log_step("Apply level filter", "SUCCESS", 'taxonomy')

      # Sorting
      try:
        sort_col = col_map.get(sort_by, None)
        if sort_by == 'id':
          sort_col = Taxonomy.id
        if sort_col is None:
          sort_col = Taxonomy.id

        if sort_dir.lower() == 'desc':
          query = query.order_by(sort_col.desc())
        else:
          query = query.order_by(sort_col.asc())
      except Exception:
        # fall back silently
        query = query.order_by(Taxonomy.id.asc())

      # Paginate
      log_step("Execute pagination query", "START", 'taxonomy')
      log_database_operation("SELECT", "taxonomies", 'taxonomy',
                             operation="paginate", page=page, per_page=per_page)
      pagination = query.paginate(
          page=page, per_page=per_page, error_out=False)
      log_step("Execute pagination query", "SUCCESS", 'taxonomy',
               total_found=pagination.total, pages=pagination.pages)

      log_step("Convert taxonomies to dict", "START", 'taxonomy')
      taxonomies = [tax.to_dict() for tax in pagination.items]
      log_step("Convert taxonomies to dict", "SUCCESS", 'taxonomy',
               items_converted=len(taxonomies))

      result = {
          'taxonomies': taxonomies,
          'total_count': pagination.total,
          'page': page,
          'per_page': per_page,
          'pages': pagination.pages,
          'sort_by': sort_by,
          'sort_dir': sort_dir
      }

      log_api_response(200, '/taxonomy', 'taxonomy',
                       total_returned=len(taxonomies), total_count=pagination.total)
      return result

    except Exception as e:
      log_error(e, "Failed to fetch taxonomies", 'taxonomy',
                user_id=current_user.id, page=page, per_page=per_page)
      log_api_response(500, '/taxonomy', 'taxonomy', error=str(e))
      current_app.logger.error(f"Error fetching taxonomies: {e}")
      return {'message': 'Failed to fetch taxonomies'}, 500


@taxonomy_ns.route('/delete-all')
class TaxonomyDeleteAll(Resource):
  """Delete all taxonomies for current user"""

  @taxonomy_ns.doc('delete_all_taxonomies')
  @login_required
  @log_function('taxonomy')
  def delete(self):
    """Delete all taxonomy records for the current user"""
    log_api_request('DELETE', '/taxonomy/delete-all', 'taxonomy',
                    user_id=current_user.id, user_email=current_user.email)

    try:
      log_step("Count existing records", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="count_user_taxonomies")
      taxonomy_count = Taxonomy.query.filter_by(user_id=current_user.id).count()

      log_database_operation("COUNT", "bracken_results", 'taxonomy',
                             user_id=current_user.id, operation="count_user_bracken")
      bracken_count = BrackenResult.query.filter_by(
          user_id=current_user.id).count()

      log_step("Count existing records", "SUCCESS", 'taxonomy',
               taxonomy_count=taxonomy_count, bracken_count=bracken_count)

      if taxonomy_count == 0 and bracken_count == 0:
        log_warning("No taxonomy data found to delete", 'taxonomy',
                    user_id=current_user.id, user_email=current_user.email)
        log_api_response(200, '/taxonomy/delete-all', 'taxonomy',
                         message="No data to delete")
        return {'message': 'No taxonomy data found to delete'}, 200

      log_step("Begin database transaction", "START", 'taxonomy')
      log_database_operation("DELETE", "taxonomies", 'taxonomy',
                             user_id=current_user.id, records_to_delete=taxonomy_count)
      Taxonomy.query.filter_by(user_id=current_user.id).delete()

      log_database_operation("DELETE", "bracken_results", 'taxonomy',
                             user_id=current_user.id, records_to_delete=bracken_count)
      BrackenResult.query.filter_by(user_id=current_user.id).delete()

      log_step("Commit transaction", "START", 'taxonomy')
      db.session.commit()
      log_step("Commit transaction", "SUCCESS", 'taxonomy')

      log_step("Database deletion completed", "SUCCESS", 'taxonomy',
               taxonomy_deleted=taxonomy_count, bracken_deleted=bracken_count)

      current_app.logger.info(
          f"Deleted {taxonomy_count} taxonomies and {bracken_count} bracken results for user {current_user.email}")

      total_deleted = taxonomy_count + bracken_count
      result = {
          'message': f'Successfully deleted {total_deleted} taxonomy records',
          'taxonomy_deleted': taxonomy_count,
          'bracken_deleted': bracken_count,
          'total_deleted': total_deleted
      }

      log_api_response(200, '/taxonomy/delete-all', 'taxonomy',
                       total_deleted=total_deleted, taxonomy_deleted=taxonomy_count,
                       bracken_deleted=bracken_count)
      return result, 200

    except Exception as e:
      log_step("Rollback transaction", "START", 'taxonomy')
      db.session.rollback()
      log_step("Rollback transaction", "SUCCESS", 'taxonomy')

      log_error(e, "Failed to delete all taxonomies", 'taxonomy',
                user_id=current_user.id, user_email=current_user.email)
      log_api_response(500, '/taxonomy/delete-all', 'taxonomy', error=str(e))
      current_app.logger.error(f"Error deleting all taxonomies: {e}")
      return {'message': 'Failed to delete taxonomy records'}, 500


@taxonomy_ns.route('/load-default')
class TaxonomyLoadDefault(Resource):
  """Load default taxonomy data from instance/taxonomy.csv"""

  @taxonomy_ns.doc('load_default_taxonomy')
  @login_required
  @log_function('taxonomy')
  def post(self):
    """Load default taxonomy data for the current user"""
    log_api_request('POST', '/taxonomy/load-default', 'taxonomy',
                    user_id=current_user.id, user_email=current_user.email)
    try:
      # Build default file path and verify existence
      log_step("Construct default file path", "START", 'taxonomy')
      default_file_path = os.path.join(
          current_app.instance_path, 'taxonomy.csv')
      log_step("Construct default file path", "SUCCESS",
               'taxonomy', file_path=default_file_path)

      log_step("Check file existence", "START", 'taxonomy')
      log_file_operation("CHECK_EXISTS", default_file_path, 'taxonomy')
      if not os.path.exists(default_file_path):
        log_warning("Default taxonomy file not found",
                    'taxonomy', file_path=default_file_path)
        log_api_response(404, '/taxonomy/load-default',
                         'taxonomy', error="Default file not found")
        return {'message': 'Default taxonomy file not found'}, 404
      log_step("Check file existence", "SUCCESS", 'taxonomy')

      # Count and remove existing taxonomy entries for this user
      log_step("Count existing records", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="count_before_replace")
      existing_count = Taxonomy.query.filter_by(user_id=current_user.id).count()
      log_step("Count existing records", "SUCCESS",
               'taxonomy', existing_count=existing_count)

      log_step("Clear existing taxonomy data", "START", 'taxonomy')
      log_database_operation("DELETE", "taxonomies", 'taxonomy',
                             user_id=current_user.id, records_to_delete=existing_count)
      Taxonomy.query.filter_by(user_id=current_user.id).delete()
      db.session.commit()
      post_delete_count = Taxonomy.query.filter_by(
          user_id=current_user.id).count()
      log_step("Clear existing taxonomy data", "SUCCESS", 'taxonomy',
               confirmed_deleted=existing_count - post_delete_count, remaining_after_delete=post_delete_count)

      # Load CSV into DataFrame and normalize
      log_step("Load CSV file", "START", 'taxonomy')
      log_file_operation("READ_CSV", default_file_path, 'taxonomy')
      df = pd.read_csv(default_file_path)
      log_step("Load CSV file", "SUCCESS", 'taxonomy',
               file_shape=df.shape, columns=list(df.columns))

      current_app.logger.info(
          f"Loading default taxonomy from {default_file_path}, shape: {df.shape}")

      # Normalize NaNs to None for mapping
      df = df.where(pd.notnull(df), None)

      # Use model helper to perform bulk creation; it will handle per-row errors and logging
      log_step("Process dataframe rows", "START",
               'taxonomy', total_rows=len(df))
      created = Taxonomy.bulk_create_from_dataframe(current_user.id, df)
      records_added = len(created)
      # Commit final changes
      db.session.commit()

      failed_records = max(0, len(df) - records_added)
      total_after = Taxonomy.query.filter_by(user_id=current_user.id).count()

      log_step("Process dataframe rows", "SUCCESS", 'taxonomy', total_rows=len(
          df), records_added=records_added, failed_records=failed_records, total_after=total_after)

      current_app.logger.info(
          f"Loaded {records_added} default taxonomies for user {current_user.email}, replaced {existing_count}, total_after={total_after}")

      result = {
          'message': f'Successfully loaded {records_added} default taxonomy records',
          'records_added': records_added,
          'previous_records_replaced': existing_count,
          'failed_records': failed_records,
          'total_after': total_after
      }

      log_api_response(200, '/taxonomy/load-default', 'taxonomy', records_added=records_added,
                       previous_replaced=existing_count, failed_records=failed_records)
      return result, 200

    except Exception as e:
      # Rollback and report
      log_step("Rollback transaction", "START", 'taxonomy')
      db.session.rollback()
      log_step("Rollback transaction", "SUCCESS", 'taxonomy')

      log_error(e, "Failed to load default taxonomy", 'taxonomy',
                user_id=current_user.id, file_path=default_file_path)
      log_api_response(500, '/taxonomy/load-default', 'taxonomy', error=str(e))
      current_app.logger.error(f"Error loading default taxonomy: {e}")
      return {'message': f'Failed to load default taxonomy: {str(e)}'}, 500


@taxonomy_ns.route('/statistics')
class TaxonomyStatistics(Resource):
  """Taxonomy statistics endpoint"""

  @taxonomy_ns.doc('taxonomy_statistics')
  @login_required
  @log_function('taxonomy')
  def get(self):
    """Get taxonomy statistics for current user"""
    log_api_request('GET', '/taxonomy/statistics', 'taxonomy',
                    user_id=current_user.id, user_email=current_user.email)

    try:
      log_step("Calculate total taxonomies", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="total_count")
      total_taxonomies = Taxonomy.query.filter_by(
          user_id=current_user.id).count()
      log_step("Calculate total taxonomies", "SUCCESS", 'taxonomy',
               total_taxonomies=total_taxonomies)

      log_step("Calculate species count", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="species_count",
                             filter="species NOT NULL AND species != ''")
      species_count = Taxonomy.query.filter_by(
          user_id=current_user.id,
          species=db.not_(None)
      ).filter(Taxonomy.species != '').count()
      log_step("Calculate species count", "SUCCESS", 'taxonomy',
               species_count=species_count)

      log_step("Calculate genus count", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="genus_count")
      genus_count = Taxonomy.query.filter_by(
          user_id=current_user.id,
          genus=db.not_(None)
      ).filter(Taxonomy.genus != '').count()
      log_step("Calculate genus count", "SUCCESS", 'taxonomy',
               genus_count=genus_count)

      log_step("Calculate family count", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="family_count")
      family_count = Taxonomy.query.filter_by(
          user_id=current_user.id,
          family=db.not_(None)
      ).filter(Taxonomy.family != '').count()
      log_step("Calculate family count", "SUCCESS", 'taxonomy',
               family_count=family_count)

      log_step("Calculate phylum count", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="phylum_count")
      phylum_count = Taxonomy.query.filter_by(
          user_id=current_user.id,
          phylum=db.not_(None)
      ).filter(Taxonomy.phylum != '').count()
      log_step("Calculate phylum count", "SUCCESS", 'taxonomy',
               phylum_count=phylum_count)

      log_step("Calculate domain count", "START", 'taxonomy')
      log_database_operation("COUNT", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="domain_count")
      domain_count = Taxonomy.query.filter_by(
          user_id=current_user.id,
          domain=db.not_(None)
      ).filter(Taxonomy.domain != '').count()
      log_step("Calculate domain count", "SUCCESS", 'taxonomy',
               domain_count=domain_count)

      log_step("Calculate abundance statistics", "START", 'taxonomy')
      log_database_operation("AGGREGATE", "taxonomies", 'taxonomy',
                             user_id=current_user.id, operation="abundance_statistics",
                             functions="AVG(total_abundance,mean_abundance,prevalence),COUNT(id)")
      abundance_stats = db.session.query(
          db.func.avg(Taxonomy.total_abundance).label('avg_total_abundance'),
          db.func.avg(Taxonomy.mean_abundance).label('avg_mean_abundance'),
          db.func.avg(Taxonomy.prevalence).label('avg_prevalence'),
          db.func.count(Taxonomy.id).label('total_records')
      ).filter_by(user_id=current_user.id).first()
      # Handle case where query returns None
      if not abundance_stats:
        avg_total = 0.0
        avg_mean = 0.0
        avg_prev = 0.0
        total_rec = 0
      else:
        avg_total = float(abundance_stats.avg_total_abundance or 0)
        avg_mean = float(abundance_stats.avg_mean_abundance or 0)
        avg_prev = float(abundance_stats.avg_prevalence or 0)
        total_rec = int(abundance_stats.total_records or 0)

      log_step("Calculate abundance statistics", "SUCCESS", 'taxonomy',
               avg_total_abundance=avg_total,
               avg_mean_abundance=avg_mean,
               avg_prevalence=avg_prev,
               total_records=total_rec)

      result = {
          'total_taxonomies': total_taxonomies,
          'by_level': {
              'species': species_count,
              'genus': genus_count,
              'family': family_count,
              'phylum': phylum_count,
              'domain': domain_count
          },
          'abundance_stats': {
              'avg_total_abundance': avg_total,
              'avg_mean_abundance': avg_mean,
              'avg_prevalence': avg_prev,
              'total_records': total_rec
          }
      }

      log_api_response(200, '/taxonomy/statistics', 'taxonomy',
                       total_taxonomies=total_taxonomies, species_count=species_count,
                       genus_count=genus_count, family_count=family_count)
      return result, 200

    except Exception as e:
      log_error(e, "Failed to fetch taxonomy statistics", 'taxonomy',
                user_id=current_user.id, user_email=current_user.email)
      log_api_response(500, '/taxonomy/statistics', 'taxonomy', error=str(e))
      current_app.logger.error(f"Error fetching taxonomy statistics: {e}")
      return {'message': 'Failed to fetch taxonomy statistics'}, 500
