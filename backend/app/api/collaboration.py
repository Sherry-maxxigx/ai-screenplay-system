from fastapi import APIRouter, Body
from typing import Dict, Any
from app.core.collaboration import co_creation_engine

router = APIRouter()

@router.post('/sync_edit')
async def sync_edit(edit_data: Dict[str, Any] = Body(...)):
    """500ms 定频增量同步编辑，返回影响范围"""
    return await co_creation_engine.process_incremental_edit(edit_data)

@router.post('/toggle_lock')
async def toggle_lock(lock_data: Dict[str, Any] = Body(...)):
    """处理用户框选锁定逻辑"""
    return await co_creation_engine.toggle_narrative_lock(lock_data)

@router.post('/adapt')
async def adapt_content(adapt_req: Dict[str, Any] = Body(...)):
    """用户确认后的定向修改应用"""
    return await co_creation_engine.confirm_adaptation(adapt_req)
