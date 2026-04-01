from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.core.config import settings

# 创建FastAPI应用实例
app = FastAPI(
    title="AI剧本协同创作系统API",
    description="基于AI原生架构的专业剧本协同创作系统后端API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api")

# 根路径
@app.get("/")
def read_root():
    return {"message": "AI剧本协同创作系统API", "version": "1.0.0"}

# 健康检查
@app.get("/health")
def health_check():
    return {"status": "healthy"}
  
