from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# MongoDB async client
client = None
db = None

def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    print("Connected to MongoDB.")

def close_mongo_connection():
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")

def get_mongo_db():
    return db

# Definitions for unstructured tables (managed dynamically or via models like Pydantic, but let's define their purpose here)

# Collections:
# 1. 'screenplays': 存储剧本正文信息 (Store core screenplay texts)
# 2. 'versions': 存储版本记录 (Store version history)
# 3. 'traces': 存储修改痕迹 (Store modification traces for co-creation)

async def init_mongo_indexes():
    """Initialize essential MongoDB indexes"""
    if db is not None:
        await db.screenplays.create_index("project_id")
        await db.versions.create_index([("project_id", 1), ("version_number", -1)])
        await db.traces.create_index("screenplay_id")
        print("MongoDB Indexes initialized.")
    else:
        print("MongoDB db instance not found! Please connect first.")
