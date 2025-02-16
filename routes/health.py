from flask import jsonify
from flask import current_app
from flask import Blueprint
from integrations.weaviate_schema import WeaviateSchema

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health')
def health_check():
    try:
        weaviate_client = current_app.config.get('weaviate_client')
        if not weaviate_client:
            raise Exception("Weaviate client not initialized")
            
        schema_manager = WeaviateSchema(weaviate_client.client)
        
        schema_status = {
            'collections': {
                'TestCase': weaviate_client.client.collections.exists("TestCase"),
                'Metadata': weaviate_client.client.collections.exists("Metadata")
            },
            'version': schema_manager.current_version
        }
        
        return jsonify({
            'weaviate': {
                'connected': True,
                'schema': schema_status
            }
        })
    except Exception as e:
        return jsonify({
            'weaviate': {
                'connected': False,
                'error': str(e)
            }
        }), 503 