"""Unit tests for identity management service"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.identity_service import IdentityService
from app.models.identity import Identity, IdentityStatus


@pytest.fixture
def identity_service():
    """Create identity service instance"""
    return IdentityService()


@pytest.fixture
def sample_identity():
    """Create a sample identity"""
    return Identity(
        unique_id=str(uuid.uuid4()),
        status=IdentityStatus.ACTIVE,
        application_ids=["app-001"],
        metadata={}
    )


@pytest.fixture
def sample_embedding():
    """Create a sample embedding"""
    return [0.1] * 512


@pytest.fixture
def sample_bounding_box():
    """Create a sample bounding box"""
    return {"x": 100, "y": 100, "width": 200, "height": 200}


class TestUniqueIDGeneration:
    """Tests for unique ID generation"""
    
    def test_generate_unique_id_format(self, identity_service):
        """Test that generated ID is valid UUID v4"""
        unique_id = identity_service.generate_unique_id()
        
        # Should be valid UUID
        uuid_obj = uuid.UUID(unique_id)
        assert str(uuid_obj) == unique_id
        assert uuid_obj.version == 4
    
    def test_generate_unique_id_uniqueness(self, identity_service):
        """Test that multiple generated IDs are unique"""
        ids = set()
        for _ in range(100):
            unique_id = identity_service.generate_unique_id()
            ids.add(unique_id)
        
        # All IDs should be unique
        assert len(ids) == 100
    
    @pytest.mark.asyncio
    async def test_create_identity_generates_unique_id(self, identity_service):
        """Test that create_identity generates a unique ID"""
        with patch('app.database.repositories.identity_repository.get_by_unique_id', 
                  new_callable=AsyncMock, return_value=None):
            with patch('app.database.repositories.identity_repository.create', 
                      new_callable=AsyncMock):
                identity = await identity_service.create_identity("app-001")
                
                # Should have valid UUID
                uuid_obj = uuid.UUID(identity.unique_id)
                assert uuid_obj.version == 4
    
    @pytest.mark.asyncio
    async def test_create_identity_handles_collision(self, identity_service):
        """Test that UUID collision is handled by regenerating"""
        existing_identity = Identity(
            unique_id=str(uuid.uuid4()),
            status=IdentityStatus.ACTIVE,
            application_ids=[]
        )
        
        # First call returns existing, second returns None
        with patch('app.database.repositories.identity_repository.get_by_unique_id',
                  new_callable=AsyncMock, side_effect=[existing_identity, None]):
            with patch('app.database.repositories.identity_repository.create',
                      new_callable=AsyncMock):
                identity = await identity_service.create_identity("app-001")
                
                # Should have generated different ID
                assert identity.unique_id != existing_identity.unique_id


class TestIdentityCreation:
    """Tests for identity creation"""
    
    @pytest.mark.asyncio
    async def test_create_identity_success(self, identity_service):
        """Test successful identity creation"""
        with patch('app.database.repositories.identity_repository.get_by_unique_id',
                  new_callable=AsyncMock, return_value=None):
            with patch('app.database.repositories.identity_repository.create',
                      new_callable=AsyncMock):
                identity = await identity_service.create_identity("app-001")
                
                assert identity.unique_id is not None
                assert identity.status == IdentityStatus.ACTIVE
                assert "app-001" in identity.application_ids
    
    @pytest.mark.asyncio
    async def test_create_identity_with_metadata(self, identity_service):
        """Test identity creation with metadata"""
        metadata = {"source": "test", "priority": "high"}
        
        with patch('app.database.repositories.identity_repository.get_by_unique_id',
                  new_callable=AsyncMock, return_value=None):
            with patch('app.database.repositories.identity_repository.create',
                      new_callable=AsyncMock):
                identity = await identity_service.create_identity("app-001", metadata)
                
                assert identity.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_create_identity_failure(self, identity_service):
        """Test identity creation failure handling"""
        with patch('app.database.repositories.identity_repository.get_by_unique_id',
                  new_callable=AsyncMock, return_value=None):
            with patch('app.database.repositories.identity_repository.create',
                      new_callable=AsyncMock, side_effect=Exception("Database error")):
                with pytest.raises(ValueError, match="Identity creation failed"):
                    await identity_service.create_identity("app-001")


class TestIdentityEmbeddingAssociation:
    """Tests for identity-embedding association"""
    
    @pytest.mark.asyncio
    async def test_link_embedding_to_identity(self, identity_service, 
                                             sample_embedding, sample_bounding_box):
        """Test linking embedding to identity"""
        with patch('app.services.embedding_storage_service.embedding_storage_service.store_embedding',
                  new_callable=AsyncMock, return_value=True):
            success = await identity_service.link_embedding_to_identity(
                identity_id="id-001",
                application_id="app-001",
                embedding=sample_embedding,
                bounding_box=sample_bounding_box,
                quality_score=0.95
            )
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_get_identity_by_application(self, identity_service, sample_identity):
        """Test retrieving identity by application ID"""
        from app.models.identity import IdentityEmbedding, EmbeddingMetadata, FaceBoundingBox
        
        embedding = IdentityEmbedding(
            identity_id=sample_identity.unique_id,
            application_id="app-001",
            embedding_vector=[0.1] * 512,
            metadata=EmbeddingMetadata(
                model_version="facenet-v1",
                quality_score=0.95,
                face_box=FaceBoundingBox(x=100, y=100, width=200, height=200)
            )
        )
        
        with patch('app.database.repositories.embedding_repository.get_by_application_id',
                  new_callable=AsyncMock, return_value=embedding):
            with patch('app.database.repositories.identity_repository.get_by_unique_id',
                      new_callable=AsyncMock, return_value=sample_identity):
                identity = await identity_service.get_identity_by_application("app-001")
                
                assert identity is not None
                assert identity.unique_id == sample_identity.unique_id
    
    @pytest.mark.asyncio
    async def test_create_or_link_identity_new(self, identity_service,
                                               sample_embedding, sample_bounding_box):
        """Test creating new identity for unique applicant"""
        with patch.object(identity_service, 'create_identity',
                         new_callable=AsyncMock) as mock_create:
            with patch.object(identity_service, 'link_embedding_to_identity',
                            new_callable=AsyncMock, return_value=True):
                mock_identity = Identity(
                    unique_id="new-id",
                    status=IdentityStatus.ACTIVE,
                    application_ids=["app-001"]
                )
                mock_create.return_value = mock_identity
                
                identity_id = await identity_service.create_or_link_identity(
                    application_id="app-001",
                    embedding=sample_embedding,
                    bounding_box=sample_bounding_box,
                    quality_score=0.95,
                    is_duplicate=False
                )
                
                assert identity_id == "new-id"
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_or_link_identity_duplicate(self, identity_service, sample_identity,
                                                     sample_embedding, sample_bounding_box):
        """Test linking to existing identity for duplicate"""
        with patch.object(identity_service, 'get_identity_by_application',
                         new_callable=AsyncMock, return_value=sample_identity):
            with patch.object(identity_service, 'add_application_to_identity',
                            new_callable=AsyncMock, return_value=True):
                with patch.object(identity_service, 'link_embedding_to_identity',
                                new_callable=AsyncMock, return_value=True):
                    identity_id = await identity_service.create_or_link_identity(
                        application_id="app-002",
                        embedding=sample_embedding,
                        bounding_box=sample_bounding_box,
                        quality_score=0.95,
                        is_duplicate=True,
                        matched_application_id="app-001"
                    )
                    
                    assert identity_id == sample_identity.unique_id


class TestDuplicateLinking:
    """Tests for duplicate application linking"""
    
    @pytest.mark.asyncio
    async def test_mark_application_as_duplicate(self, identity_service):
        """Test marking application as duplicate"""
        with patch('app.database.repositories.application_repository.update_status',
                  new_callable=AsyncMock):
            with patch('app.database.repositories.application_repository.update_result',
                      new_callable=AsyncMock):
                with patch('app.database.repositories.application_repository.update_processing_metadata',
                          new_callable=AsyncMock):
                    success = await identity_service.mark_application_as_duplicate(
                        application_id="app-002",
                        identity_id="id-001",
                        matched_application_id="app-001",
                        confidence_score=0.95
                    )
                    
                    assert success is True
    
    @pytest.mark.asyncio
    async def test_mark_application_as_verified(self, identity_service):
        """Test marking application as verified"""
        with patch('app.database.repositories.application_repository.update_status',
                  new_callable=AsyncMock):
            with patch('app.database.repositories.application_repository.update_result',
                      new_callable=AsyncMock):
                with patch('app.database.repositories.application_repository.update_processing_metadata',
                          new_callable=AsyncMock):
                    success = await identity_service.mark_application_as_verified(
                        application_id="app-001",
                        identity_id="id-001"
                    )
                    
                    assert success is True


class TestIdentityStatusManagement:
    """Tests for identity status management"""
    
    @pytest.mark.asyncio
    async def test_suspend_identity(self, identity_service, sample_identity):
        """Test suspending an identity"""
        with patch('app.database.repositories.identity_repository.update_status',
                  new_callable=AsyncMock, return_value=True):
            with patch.object(identity_service, 'get_identity',
                            new_callable=AsyncMock, return_value=sample_identity):
                with patch('app.database.repositories.identity_repository.update_metadata',
                          new_callable=AsyncMock, return_value=True):
                    success = await identity_service.suspend_identity(
                        sample_identity.unique_id,
                        "Suspicious activity"
                    )
                    
                    assert success is True
    
    @pytest.mark.asyncio
    async def test_reactivate_identity(self, identity_service, sample_identity):
        """Test reactivating a suspended identity"""
        sample_identity.status = IdentityStatus.SUSPENDED
        
        with patch('app.database.repositories.identity_repository.update_status',
                  new_callable=AsyncMock, return_value=True):
            with patch.object(identity_service, 'get_identity',
                            new_callable=AsyncMock, return_value=sample_identity):
                with patch('app.database.repositories.identity_repository.update_metadata',
                          new_callable=AsyncMock, return_value=True):
                    success = await identity_service.reactivate_identity(
                        sample_identity.unique_id
                    )
                    
                    assert success is True
    
    @pytest.mark.asyncio
    async def test_validate_unique_id_active(self, identity_service, sample_identity):
        """Test validating an active identity"""
        with patch('app.database.repositories.identity_repository.get_by_unique_id',
                  new_callable=AsyncMock, return_value=sample_identity):
            is_valid = await identity_service.validate_unique_id(sample_identity.unique_id)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_unique_id_suspended(self, identity_service, sample_identity):
        """Test validating a suspended identity"""
        sample_identity.status = IdentityStatus.SUSPENDED
        
        with patch('app.database.repositories.identity_repository.get_by_unique_id',
                  new_callable=AsyncMock, return_value=sample_identity):
            is_valid = await identity_service.validate_unique_id(sample_identity.unique_id)
            
            assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
