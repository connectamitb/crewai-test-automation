import pytest
from integrations.weaviate_schema import WeaviateSchema
from integrations.weaviate_integration import WeaviateIntegration

@pytest.fixture
def weaviate_client():
    return WeaviateIntegration()

def test_schema_initialization(weaviate_client):
    """Test schema initialization"""
    schema_manager = WeaviateSchema(weaviate_client.client)
    
    # Ensure schema exists
    schema_manager.ensure_schema()
    
    # Verify TestCase collection exists
    assert weaviate_client.client.collections.exists("TestCase")
    
    # Verify Metadata collection exists
    assert weaviate_client.client.collections.exists("Metadata")
    
    # Verify schema version is stored
    metadata = weaviate_client.client.collections.get("Metadata")
    version_obj = metadata.query.fetch_objects(
        "value", 
        where={"path": ["key"], "operator": "Equal", "valueText": "schema_version"}
    )
    assert version_obj.objects[0].properties["value"] == "1.0"

def test_schema_idempotency(weaviate_client):
    """Test that ensuring schema multiple times is safe"""
    schema_manager = WeaviateSchema(weaviate_client.client)
    
    # Call ensure_schema multiple times
    schema_manager.ensure_schema()
    schema_manager.ensure_schema()
    
    # Should not raise any errors
    assert True 