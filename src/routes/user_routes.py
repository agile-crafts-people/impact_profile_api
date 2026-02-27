"""
User routes for Flask API.

Provides endpoints for User domain:
- POST /api/user - Create a new user document
- GET /api/user - Get all user documents (with optional ?name= query parameter)
- GET /api/user/<id> - Get a specific user document by ID
- PATCH /api/user/<id> - Update a user document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.user_service import UserService

import logging
logger = logging.getLogger(__name__)


def create_user_routes():
    """
    Create a Flask Blueprint exposing user endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with user routes
    """
    user_routes = Blueprint('user_routes', __name__)
    
    @user_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_user():
        """
        POST /api/user - Create a new user document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created user document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        user_id = UserService.create_user(data, token, breadcrumb)
        user = UserService.get_user(user_id, token, breadcrumb)
        
        logger.info(f"create_user Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(user), 201
    
    @user_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_users():
        """
        GET /api/user - Retrieve infinite scroll batch of sorted, filtered user documents.
        
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
        result = UserService.get_users(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_users Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @user_routes.route('/<user_id>', methods=['GET'])
    @handle_route_exceptions
    def get_user(user_id):
        """
        GET /api/user/<id> - Retrieve a specific user document by ID.
        
        Args:
            user_id: The user ID to retrieve
            
        Returns:
            JSON response with the user document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        user = UserService.get_user(user_id, token, breadcrumb)
        logger.info(f"get_user Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(user), 200
    
    @user_routes.route('/<user_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_user(user_id):
        """
        PATCH /api/user/<id> - Update a user document.
        
        Args:
            user_id: The user ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated user document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        user = UserService.update_user(user_id, data, token, breadcrumb)
        
        logger.info(f"update_user Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(user), 200
    
    logger.info("User Flask Routes Registered")
    return user_routes