import os

yaml_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\docker-compose.yml"
with open(yaml_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('neo4j:4.4', 'neo4j:5-community')
if '      - milvus\n' not in text:
    text = text.replace('      - neo4j\n', '      - neo4j\n      - milvus\n')
if '- MILVUS_HOST=milvus' not in text:
    text = text.replace('      - NEO4J_PASSWORD=password\n', '      - NEO4J_PASSWORD=password\n      - MILVUS_HOST=milvus\n      - MILVUS_PORT=19530\n')

old_milvus = """  # Milvus向量数据库（暂时注释，网络连接问题）
  # milvus:
  #   image: milvusdb/milvus:v2.2.11
  #   ports:
  #     - "19530:19530"
  #     - "9091:9091"
  #   volumes:
  #     - milvus-data:/var/lib/milvus
  #   networks:
  #     - screenplay-network"""

new_milvus = """  # Milvus向量数据库
  milvus:
    image: milvusdb/milvus:v2.2.11
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_USE_EMBED: "true"
      MINIO_ADDRESS: localhost
    ports:
      - "19530:19530"
      - "9091:9091"
    volumes:
      - milvus-data:/var/lib/milvus
    networks:
      - screenplay-network"""

text = text.replace(old_milvus, new_milvus)
text = text.replace('  neo4j-data:\n\n', '  neo4j-data:\n  milvus-data:\n\n')

with open(yaml_path, 'w', encoding='utf-8') as f:
    f.write(text)
