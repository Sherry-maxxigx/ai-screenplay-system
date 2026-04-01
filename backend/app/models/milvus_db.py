from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from app.core.config import settings

def connect_to_milvus():
    connections.connect("default", host=settings.MILVUS_HOST, port=str(settings.MILVUS_PORT))
    print(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")

def disconnect_milvus():
    connections.disconnect("default")
    print("Milvus connection closed.")

def init_milvus_collections():
    """Initialize Milvus collections for Narrative Fingerprints and Semantic Search"""
    collection_name = "narrative_fingerprints"
    
    if utility.has_collection(collection_name):
        print(f"Milvus Collection '{collection_name}' already exists.")
        return

    # Schema definition for Narrative Fingerprint (创新点③：基于叙事指纹的剧本全链路价值保障体系)
    # primary_key: id
    # project_id: link to project
    # fingerprint_vector: 叙事特征向量表达 (e.g. 1536 dim for OpenAI text-embedding-3-small)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="project_id", dtype=DataType.INT64, description="Project ID linking to MySQL"),
        FieldSchema(name="fingerprint_vector", dtype=DataType.FLOAT_VECTOR, dim=1536, description="Narrative fingerprint vector"),
        FieldSchema(name="text_segment", dtype=DataType.VARCHAR, max_length=65535, description="Associated text segment")
    ]
    
    schema = CollectionSchema(fields, description="Narrative fingerprint for value assurance")
    collection = Collection(name=collection_name, schema=schema)
    
    # Create Index for fast vector search
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="fingerprint_vector", index_params=index_params)
    print(f"Milvus Collection '{collection_name}' initialized with vector index.")
