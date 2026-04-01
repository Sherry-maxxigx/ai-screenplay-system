import asyncio
from app.models.database import Base, engine
from app.models.mongo import connect_to_mongo, init_mongo_indexes, close_mongo_connection
from app.models.milvus_db import connect_to_milvus, init_milvus_collections, disconnect_milvus
from app.models.neo4j_db import neo4j_db

async def init_all_databases():
    print("=== 初始化MySQL ===")
    Base.metadata.create_all(bind=engine)
    print("MySQL: 数据表结构已创建成功。")

    print("\n=== 初始化MongoDB ===")
    try:
        connect_to_mongo()
        await init_mongo_indexes()
        close_mongo_connection()
    except Exception as e:
        print(f"MongoDB初始化失败: {e}")

    print("\n=== 初始化Neo4j ===")
    try:
        neo4j_db.connect()
        neo4j_db.init_schema()
        neo4j_db.close()
    except Exception as e:
        print(f"Neo4j初始化失败: {e}")

    print("\n=== 初始化Milvus ===")
    try:
        connect_to_milvus()
        init_milvus_collections()
        disconnect_milvus()
    except Exception as e:
        print(f"Milvus初始化失败: {e}")

if __name__ == "__main__":
    asyncio.run(init_all_databases())
    print("\n数据库初始化完成。")
