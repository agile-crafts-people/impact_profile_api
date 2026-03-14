"""
Platform routes for Flask API.

Provides endpoints for Platform domain:
- POST /api/platform - Create a new platform document
- GET /api/platform - Get all platform documents (with optional ?name= query parameter)
- GET /api/platform/<id> - Get a specific platform document by ID
- PATCH /api/platform/<id> - Update a platform document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.platform_service import PlatformService

import logging
logger = logging.getLogger(__name__)


def create_platform_routes():
    """
    Create a Flask Blueprint exposing platform endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with platform routes
    """
    platform_routes = Blueprint('platform_routes', __name__)
    
    @platform_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_platform():
        """
        POST /api/platform - Create a new platform document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created platform document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        platform_id = PlatformService.create_platform(data, token, breadcrumb)
        platform = PlatformService.get_platform(platform_id, token, breadcrumb)
        
        logger.info(f"create_platform Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(platform), 201
    
    @platform_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_platforms():
        """
        GET /api/platform - Retrieve infinite scroll batch of sorted, filtered platform documents.
        
        Query Parameters:
            name: Optional name filter
            after_id: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
            limit: Items per batch (default: 10, max: 100)
            sort_by: Field to sort by (default: 'name')
            order: Sort order 'asc' or 'desc' (default: 'asc')
        
        Returns:
            JSON response with infinite scroll results: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None
            }
        
        Raises:
            400 Bad Request: If invalid parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Get query parameters
        name = request.args.get('name')
        after_id = request.args.get('after_id')
        limit = request.args.get('limit', 10, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        
        # Service layer validates parameters and raises HTTPBadRequest if invalid
        # @handle_route_exceptions decorator will catch and format the exception
        result = PlatformService.get_platforms(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_platforms Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @platform_routes.route('/<platform_id>', methods=['GET'])
    @handle_route_exceptions
    def get_platform(platform_id):
        """
        GET /api/platform/<id> - Retrieve a specific platform document by ID.
        
        Args:
            platform_id: The platform ID to retrieve
            
        Returns:
            JSON response with the platform document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        platform = PlatformService.get_platform(platform_id, token, breadcrumb)
        logger.info(f"get_platform Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(platform), 200
    
    @platform_routes.route('/<platform_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_platform(platform_id):
        """
        PATCH /api/platform/<id> - Update a platform document.
        
        Args:
            platform_id: The platform ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated platform document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        platform = PlatformService.update_platform(platform_id, data, token, breadcrumb)
        
        logger.info(f"update_platform Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(platform), 200
    
    logger.info("Platform Flask Routes Registered")
    return platform_routes