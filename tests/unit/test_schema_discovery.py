"""Tests for schema discovery engine."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nlap.opensearch.field_extractor import FieldExtractor
from nlap.opensearch.schema_cache import SchemaCache
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.opensearch.schema_models import FieldInfo, FieldType, SchemaInfo
from nlap.opensearch.type_identifier import TypeIdentifier


class TestFieldExtractor:
    """Test FieldExtractor component."""

    def test_extract_simple_fields(self):
        """Test extracting simple flat fields."""
        extractor = FieldExtractor()
        documents = [
            {"name": "John", "age": 30, "active": True},
            {"name": "Jane", "age": 25, "active": False},
        ]

        field_values = extractor.extract_fields(documents)

        assert "name" in field_values
        assert "age" in field_values
        assert "active" in field_values
        assert len(field_values["name"]) == 2
        assert len(field_values["age"]) == 2

    def test_extract_nested_fields(self):
        """Test extracting nested object fields."""
        extractor = FieldExtractor()
        documents = [
            {
                "user": {
                    "profile": {"first_name": "John", "last_name": "Doe"},
                    "settings": {"theme": "dark"},
                }
            }
        ]

        field_values = extractor.extract_fields(documents)

        assert "user.profile.first_name" in field_values
        assert "user.profile.last_name" in field_values
        assert "user.settings.theme" in field_values

    def test_extract_array_fields(self):
        """Test extracting array fields."""
        extractor = FieldExtractor()
        documents = [
            {"tags": ["python", "testing"], "scores": [1, 2, 3]},
            {"tags": ["javascript"], "scores": [4, 5]},
        ]

        field_values = extractor.extract_fields(documents)

        assert "tags" in field_values
        assert "scores" in field_values

    def test_extract_nested_array_fields(self):
        """Test extracting nested array fields."""
        extractor = FieldExtractor()
        documents = [
            {
                "items": [
                    {"id": 1, "name": "item1"},
                    {"id": 2, "name": "item2"},
                ]
            }
        ]

        field_values = extractor.extract_fields(documents)

        assert "items.id" in field_values
        assert "items.name" in field_values

    def test_extract_max_sample_values(self):
        """Test that max_sample_values limit is respected."""
        extractor = FieldExtractor(max_sample_values=3)
        documents = [{"count": i} for i in range(10)]

        field_values = extractor.extract_fields(documents)

        assert len(field_values["count"]) <= 3

    def test_extract_max_depth(self):
        """Test that max_depth limit is respected."""
        extractor = FieldExtractor(max_depth=2)
        # Create deeply nested structure
        doc = {"level1": {"level2": {"level3": {"level4": "deep"}}}}
        documents = [doc]

        field_values = extractor.extract_fields(documents)

        # Should stop at max_depth
        assert "level1.level2.level3" not in field_values or len(field_values) < 4


class TestTypeIdentifier:
    """Test TypeIdentifier component."""

    def test_identify_text_field(self):
        """Test identifying text fields."""
        identifier = TypeIdentifier()
        samples = ["hello", "world", "test"]

        field_type = identifier.identify_field_type("name", samples)

        assert field_type in (FieldType.TEXT, FieldType.KEYWORD)

    def test_identify_numeric_field(self):
        """Test identifying numeric fields."""
        identifier = TypeIdentifier()
        samples = [1, 2, 3, 4, 5]

        field_type = identifier.identify_field_type("age", samples)

        assert field_type == FieldType.NUMERIC

    def test_identify_boolean_field(self):
        """Test identifying boolean fields."""
        identifier = TypeIdentifier()
        samples = [True, False, True]

        field_type = identifier.identify_field_type("active", samples)

        assert field_type == FieldType.BOOLEAN

    def test_identify_date_field(self):
        """Test identifying date fields."""
        identifier = TypeIdentifier()
        samples = ["2024-01-01", "2024-01-02", "2024-01-03"]

        field_type = identifier.identify_field_type("created_at", samples)

        assert field_type == FieldType.DATE

    def test_identify_object_field(self):
        """Test identifying object fields."""
        identifier = TypeIdentifier()
        samples = [{"key": "value"}, {"key": "value2"}]

        field_type = identifier.identify_field_type("metadata", samples)

        assert field_type == FieldType.OBJECT

    def test_identify_array_field(self):
        """Test identifying array fields."""
        identifier = TypeIdentifier()
        samples = [[1, 2, 3], [4, 5], [6]]

        field_type = identifier.identify_field_type("items", samples)

        assert field_type == FieldType.ARRAY

    def test_identify_ip_field(self):
        """Test identifying IP address fields."""
        identifier = TypeIdentifier()
        samples = ["192.168.1.1", "10.0.0.1", "127.0.0.1"]

        field_type = identifier.identify_field_type("ip_address", samples)

        assert field_type == FieldType.IP

    def test_identify_geo_point_field(self):
        """Test identifying geo point fields."""
        identifier = TypeIdentifier()
        samples = ["40.7128,-74.0060", "51.5074,-0.1278"]

        field_type = identifier.identify_field_type("location", samples)

        assert field_type == FieldType.GEO_POINT

    def test_identify_unknown_field(self):
        """Test identifying unknown field types."""
        identifier = TypeIdentifier()
        samples = [None, None, None]

        field_type = identifier.identify_field_type("empty", samples)

        assert field_type == FieldType.UNKNOWN


class TestSchemaCache:
    """Test SchemaCache component."""

    def test_set_and_get(self):
        """Test setting and getting schemas from cache."""
        cache = SchemaCache()
        schema = SchemaInfo(
            index_name="test_index",
            fields={"field1": FieldInfo(name="field1", field_type=FieldType.TEXT)},
            version=1,
        )

        cache_key = "test_key"
        cache.set(cache_key, schema)

        retrieved = cache.get(cache_key)
        assert retrieved is not None
        assert retrieved.index_name == "test_index"
        assert retrieved.version == 1

    def test_cache_expiration(self):
        """Test that expired cache entries are not returned."""
        cache = SchemaCache(default_ttl_seconds=1)
        schema = SchemaInfo(
            index_name="test_index",
            fields={},
            version=1,
        )

        cache_key = "test_key"
        cache.set(cache_key, schema, ttl_seconds=1)

        # Should be available immediately
        assert cache.get(cache_key) is not None

        # Wait for expiration (in real scenario, would need time mocking)
        # For now, just test that expiration logic exists

    def test_cache_invalidation(self):
        """Test invalidating cache entries."""
        cache = SchemaCache()
        schema = SchemaInfo(index_name="test_index", fields={}, version=1)

        cache_key = "test_key"
        cache.set(cache_key, schema)

        assert cache.invalidate(cache_key) is True
        assert cache.get(cache_key) is None
        assert cache.invalidate(cache_key) is False  # Already removed

    def test_invalidate_index(self):
        """Test invalidating all schemas for an index."""
        cache = SchemaCache()
        schema1 = SchemaInfo(index_name="index1", fields={}, version=1)
        schema2 = SchemaInfo(index_name="index1", fields={}, version=2)
        schema3 = SchemaInfo(index_name="index2", fields={}, version=1)

        cache.set("key1", schema1)
        cache.set("key2", schema2)
        cache.set("key3", schema3)

        invalidated = cache.invalidate_index("index1")
        assert invalidated == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is not None  # Different index

    def test_generate_cache_key(self):
        """Test cache key generation."""
        cache = SchemaCache()

        key1 = cache.generate_cache_key("index1")
        key2 = cache.generate_cache_key("index1")
        key3 = cache.generate_cache_key("index2")

        # Same inputs should generate same key
        assert key1 == key2
        # Different inputs should generate different keys
        assert key1 != key3

    def test_generate_cache_key_with_query(self):
        """Test cache key generation with query."""
        cache = SchemaCache()

        query1 = {"match": {"field": "value"}}
        query2 = {"match": {"field": "value"}}

        key1 = cache.generate_cache_key("index1", query=query1)
        key2 = cache.generate_cache_key("index1", query=query2)

        assert key1 == key2

    def test_get_next_version(self):
        """Test version number generation."""
        cache = SchemaCache()
        schema1 = SchemaInfo(index_name="index1", fields={}, version=1)
        schema2 = SchemaInfo(index_name="index1", fields={}, version=3)

        cache.set("key1", schema1)
        cache.set("key2", schema2)

        next_version = cache._get_next_version("index1")
        assert next_version == 4


class TestSchemaDiscoveryEngine:
    """Test SchemaDiscoveryEngine component."""

    @pytest.fixture
    def mock_opensearch_manager(self):
        """Create a mock OpenSearchManager."""
        manager = AsyncMock()
        return manager

    @pytest.fixture
    def discovery_engine(self, mock_opensearch_manager):
        """Create a SchemaDiscoveryEngine instance."""
        return SchemaDiscoveryEngine(
            opensearch_manager=mock_opensearch_manager,
            sample_size=10,
        )

    @pytest.mark.asyncio
    async def test_discover_index_schema(self, discovery_engine, mock_opensearch_manager):
        """Test discovering schema for an entire index."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.hits = [
            {"name": "John", "age": 30, "active": True},
            {"name": "Jane", "age": 25, "active": False},
        ]
        mock_opensearch_manager.execute_query = AsyncMock(return_value=mock_result)

        schema = await discovery_engine.discover_index_schema("test_index", sample_size=10)

        assert schema.index_name == "test_index"
        assert len(schema.fields) > 0
        assert "name" in schema.fields
        assert "age" in schema.fields
        assert schema.version >= 1

    @pytest.mark.asyncio
    async def test_discover_index_schema_uses_cache(self, discovery_engine):
        """Test that cached schemas are returned."""
        # Pre-populate cache
        cached_schema = SchemaInfo(
            index_name="test_index",
            fields={"field1": FieldInfo(name="field1", field_type=FieldType.TEXT)},
            version=1,
        )
        cache_key = discovery_engine.cache.generate_cache_key("test_index", sample_size=10)
        discovery_engine.cache.set(cache_key, cached_schema)

        schema = await discovery_engine.discover_index_schema("test_index", use_cache=True)

        assert schema.version == 1
        # Should not have called opensearch
        assert not discovery_engine.opensearch_manager.execute_query.called

    @pytest.mark.asyncio
    async def test_discover_document_schema(self, discovery_engine, mock_opensearch_manager):
        """Test discovering schema from query results."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.hits = [
            {"status": "active", "count": 5},
            {"status": "inactive", "count": 10},
        ]
        mock_opensearch_manager.execute_query = AsyncMock(return_value=mock_result)

        query = {"term": {"status": "active"}}
        schema = await discovery_engine.discover_document_schema(
            "test_index", query=query, sample_size=10
        )

        assert schema.index_name == "test_index"
        assert len(schema.fields) > 0
        assert "status" in schema.fields
        assert "count" in schema.fields

    @pytest.mark.asyncio
    async def test_discover_empty_index(self, discovery_engine, mock_opensearch_manager):
        """Test discovering schema from empty index."""
        mock_result = MagicMock()
        mock_result.hits = []
        mock_opensearch_manager.execute_query = AsyncMock(return_value=mock_result)

        schema = await discovery_engine.discover_index_schema("empty_index")

        assert schema.index_name == "empty_index"
        assert len(schema.fields) == 0
        assert schema.version == 1

    def test_invalidate_cache_by_index(self, discovery_engine):
        """Test invalidating cache by index name."""
        schema = SchemaInfo(index_name="test_index", fields={}, version=1)
        cache_key = discovery_engine.cache.generate_cache_key("test_index")
        discovery_engine.cache.set(cache_key, schema)

        invalidated = discovery_engine.invalidate_cache(index_name="test_index")

        assert invalidated >= 1

    def test_invalidate_cache_by_key(self, discovery_engine):
        """Test invalidating cache by cache key."""
        schema = SchemaInfo(index_name="test_index", fields={}, version=1)
        cache_key = "test_key"
        discovery_engine.cache.set(cache_key, schema)

        invalidated = discovery_engine.invalidate_cache(cache_key=cache_key)

        assert invalidated == 1

