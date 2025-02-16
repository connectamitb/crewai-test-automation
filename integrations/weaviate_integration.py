"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Dict, List, Optional, Union, Literal
from dataclasses import dataclass
from enum import Enum
import weaviate
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from weaviate.collections.classes.config import (
    Configure, 
    Property,
    DataType
)
from weaviate.classes.query import MetadataQuery
from .weaviate_schema import WeaviateSchema
from datetime import datetime
from dotenv import load_dotenv

class SearchType(Enum):
    EXACT = "exact"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"

@dataclass
class SearchFilter:
    field: str
    operator: Literal["Equal", "NotEqual", "GreaterThan", "GreaterThanEqual", "LessThan", "LessThanEqual", "Like", "WithinRange"]
    value: Union[str, int, float, List, None]

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    # Class constants for defaults
    DEFAULT_PROPERTIES = [
        "name", "description", "requirement", "precondition",
        "steps", "expected_results", "priority", "tags",
        "automation_status", "created_at", "updated_at"
    ]
    DEFAULT_SEARCH_LIMIT = 5

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.client = None

        try:
            # Get credentials from environment
            load_dotenv()
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")

            if not all([weaviate_url, weaviate_api_key, openai_api_key]):
                raise ValueError("Missing required environment variables")

            self.logger.info(f"Connecting to Weaviate Cloud at: {weaviate_url}")

            # Initialize client using v4 Cloud API
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=Auth.api_key(weaviate_api_key),
                headers={
                    "X-OpenAI-Api-Key": openai_api_key
                },
                additional_config=AdditionalConfig(
                    timeout=Timeout(
                        init=30,    # Connection timeout
                        query=60,   # Query operations timeout
                        insert=120  # Insert operations timeout
                    )
                )
            )

            if self.is_healthy():
                self.logger.info("✅ Connected to Weaviate Cloud")
                schema_manager = WeaviateSchema(self.client)
                schema_manager.ensure_schema()
            else:
                raise Exception("Failed to connect to Weaviate Cloud")

        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {str(e)}")
            raise

    def _create_schema(self):
        """Create test case schema in Weaviate"""
        try:
            # Delete existing schema if it exists
            collections = self.client.collections.list_all()
            if "TestCase" in collections:
                self.logger.info("Deleting existing TestCase collection...")
                self.client.collections.delete("TestCase")
                self.logger.info("✅ Existing schema deleted")

            # Create schema with proper v4 property format
            self.client.collections.create(
                name="TestCase",
                description="Collection for storing and retrieving automated test cases",
                vectorizer_config=Configure.Vectorizer.text2vec_openai(),
                generative_config=Configure.Generative.openai(),
                properties=[
                    Property(
                        name="name",
                        data_type=DataType.TEXT,
                        description="Name/title of the test case",
                        indexFilterable=True,
                        indexSearchable=True
                    ),
                    Property(
                        name="description",
                        data_type=DataType.TEXT,
                        description="Detailed description of what the test verifies",
                        indexSearchable=True
                    ),
                    Property(
                        name="requirement",
                        data_type=DataType.TEXT,
                        description="Original requirement that this test case validates",
                        indexSearchable=True
                    ),
                    Property(
                        name="precondition",
                        data_type=DataType.TEXT,
                        description="Prerequisites needed before test execution",
                        indexSearchable=True
                    ),
                    Property(
                        name="steps",
                        data_type=DataType.TEXT_ARRAY,
                        description="Ordered list of test steps to execute",
                        indexSearchable=True
                    ),
                    Property(
                        name="expected_results",
                        data_type=DataType.TEXT_ARRAY,
                        description="Expected results corresponding to each test step",
                        indexSearchable=True
                    ),
                    Property(
                        name="priority",
                        data_type=DataType.TEXT,
                        description="Test case priority (High/Medium/Low)",
                        indexFilterable=True
                    ),
                    Property(
                        name="tags",
                        data_type=DataType.TEXT_ARRAY,
                        description="Labels/categories for the test case",
                        indexFilterable=True,
                        indexSearchable=True
                    ),
                    Property(
                        name="automation_status",
                        data_type=DataType.TEXT,
                        description="Current automation status",
                        indexFilterable=True
                    ),
                    Property(
                        name="created_at",
                        data_type=DataType.DATE,
                        description="Test case creation timestamp",
                        indexFilterable=True
                    ),
                    Property(
                        name="updated_at",
                        data_type=DataType.DATE,
                        description="Last modification timestamp",
                        indexFilterable=True
                    )
                ]
            )
            self.logger.info("✅ New schema created successfully")
        except Exception as e:
            self.logger.error(f"❌ Error creating schema: {str(e)}")
            raise

    def store_test_case(self, test_case: dict) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            self.logger.info(f"Attempting to store test case: {test_case}")
            
            # Get TestCase collection
            test_cases = self.client.collections.get("TestCase")
            
            # Add timestamps if not present
            if 'created_at' not in test_case:
                test_case['created_at'] = datetime.now().isoformat()
            if 'updated_at' not in test_case:
                test_case['updated_at'] = datetime.now().isoformat()
            
            # Store the object
            result = test_cases.data.insert(test_case)
            
            # In Weaviate v4, the UUID is returned directly as a string
            if result:
                self.logger.info(f"Successfully stored test case with ID: {result}")
                return str(result)  # Convert UUID to string
            else:
                self.logger.error("Failed to get UUID from Weaviate insert")
                return None

        except Exception as e:
            self.logger.error(f"Error storing test case: {str(e)}", exc_info=True)
            raise

    def search_test_cases(
        self,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        properties: List[str] = None,
        filters: List[SearchFilter] = None,
        sort_by: str = None,
        sort_order: SortOrder = SortOrder.DESC,
        limit: int = DEFAULT_SEARCH_LIMIT,
        offset: int = 0,
        min_score: float = 0.0
    ) -> Dict[str, Union[List[Dict], Dict]]:
        """Advanced search for test cases
        
        Args:
            query: Search query text
            search_type: Type of search (exact, semantic, or hybrid)
            properties: Properties to return
            filters: List of filters to apply
            sort_by: Field to sort by
            sort_order: Sort direction
            limit: Max results to return
            offset: Number of results to skip (for pagination)
            min_score: Minimum similarity score (0-1) for semantic results
            
        Returns:
            Dict containing:
            - results: List of matching test cases
            - metadata: Search metadata (total, page, etc.)
        """
        try:
            self.logger.info(f"Performing {search_type.value} search for: {query}")
            collection = self.client.collections.get("TestCase")
            properties = properties or self.DEFAULT_PROPERTIES
            
            # Build search parameters
            search_params = {
                "limit": limit,
                "offset": offset,
                "return_metadata": MetadataQuery(distance=True),
                "return_properties": properties
            }

            # Add filters if provided
            if filters:
                where_filter = {"operator": "And", "operands": []}
                for f in filters:
                    where_filter["operands"].append({
                        "path": [f.field],
                        "operator": f.operator,
                        "valueText": f.value if isinstance(f.value, str) else None,
                        "valueInt": f.value if isinstance(f.value, int) else None,
                        "valueNumber": f.value if isinstance(f.value, float) else None,
                        "valueDate": f.value if isinstance(f.value, datetime) else None
                    })
                search_params["where_filter"] = where_filter

            # Add sorting
            if sort_by:
                search_params["sort"] = {
                    "path": [sort_by],
                    "order": sort_order.value
                }

            # Perform search based on type
            if search_type == SearchType.EXACT:
                results = collection.query.get(**search_params)
            elif search_type == SearchType.SEMANTIC:
                results = collection.query.near_text(
                    query=query,
                    **search_params
                )
            else:  # HYBRID
                # Combine BM25 and vector search
                results = collection.query.hybrid(
                    query=query,
                    alpha=0.5,  # Balance between keyword and vector search
                    **search_params
                )

            # Process results
            processed_results = []
            for obj in results.objects:
                if not hasattr(obj.metadata, 'distance') or obj.metadata.distance >= min_score:
                    result = {
                        'properties': obj.properties,
                        'id': obj.id
                    }
                    if hasattr(obj.metadata, 'distance'):
                        result['score'] = obj.metadata.distance
                    processed_results.append(result)

            # Return results with metadata
            return {
                'results': processed_results,
                'metadata': {
                    'total': len(processed_results),
                    'offset': offset,
                    'limit': limit,
                    'has_more': len(processed_results) == limit,
                    'search_type': search_type.value
                }
            }

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}", exc_info=True)
            raise

    def get_test_case_by_id(self, id: str, properties: List[str] = None) -> Optional[Dict]:
        """Get test case by ID"""
        try:
            collection = self.client.collections.get("TestCase")
            properties = properties or self.DEFAULT_PROPERTIES
            
            result = collection.query.get_by_id(
                uuid=id,
                return_properties=properties
            )
            
            return result.properties if result else None
        except Exception as e:
            self.logger.error(f"Failed to get test case by ID: {str(e)}")
            raise

    def is_healthy(self):
        """Check if Weaviate connection is healthy"""
        try:
            return self.client.is_ready()
        except Exception:
            return False

    def close(self):
        """Close the Weaviate client connection"""
        if self.client:
            self.client.close()

    def __del__(self):
        """Ensure client is properly closed"""
        if hasattr(self, 'client') and self.client:
            self.client.close()

    def get_test_case(self, name: str, semantic: bool = False, properties: List[str] = None, limit: int = 1) -> Optional[Dict]:
        """Retrieve a test case by name
        
        Args:
            name: Name or description to search for
            semantic: If True, use semantic search instead of exact match
            properties: List of properties to return (defaults to all)
            limit: Maximum number of results to return
        """
        try:
            self.logger.info(f"Attempting to retrieve test case with {'semantic search' if semantic else 'exact match'}: {name}")
            
            test_cases = self.client.collections.get("TestCase")
            properties = properties or self.DEFAULT_PROPERTIES
            
            if semantic:
                results = test_cases.query.near_text(
                    query=name,
                    limit=limit,
                    return_metadata=MetadataQuery(distance=True),
                    return_properties=properties
                )
            else:
                results = test_cases.query.get(
                    filters={
                        "path": ["name"],
                    "operator": "Equal",
                    "valueString": name
                    },
                    return_properties=properties
                )
            
            if results.objects:
                self.logger.info("✅ Successfully retrieved test case(s)")
                if semantic:
                    return [{
                        'properties': obj.properties,
                        'score': obj.metadata.distance
                    } for obj in results.objects]
                return results.objects[0].properties
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving test case: {str(e)}")
            raise

    def search_similar_test_cases(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for semantically similar test cases
        
        Args:
            query: Natural language query to search for
            limit: Maximum number of results to return
        """
        return self.get_test_case(query, semantic=True)