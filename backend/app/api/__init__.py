from fastapi import APIRouter
from app.api import projects, characters, narrative, ai, collaboration, fingerprint, auth

# 创建API路由器
router = APIRouter()

# 注册子路由
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(characters.router, prefix="/characters", tags=["characters"])
router.include_router(narrative.router, prefix="/narrative", tags=["narrative"])
router.include_router(ai.router, prefix="/ai", tags=["ai"])
router.include_router(collaboration.router, prefix="/collaboration", tags=["collaboration"])
router.include_router(fingerprint.router, prefix="/fingerprint", tags=["fingerprint"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
