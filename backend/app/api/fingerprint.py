from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import random
import hashlib
from datetime import datetime

from app.core.fingerprint import FingerprintSystem

router = APIRouter()
fingerprint_system = FingerprintSystem()

class ScriptPayload(BaseModel):
    content: str
    target_track: str = "短剧"

@router.post("/check_originality")
async def check_originality(payload: ScriptPayload):
    # 提取叙事指纹 (5维组合成的768维特征)
    fingerprint = await fingerprint_system.extract_narrative_fingerprint(payload.content)
    
    # 1. 和原创性校验子库比对
    result = await fingerprint_system.evaluate_originality(fingerprint, payload.content)
    return result

@router.post("/evaluate_professional")
async def evaluate_professional(payload: ScriptPayload):
    fingerprint = await fingerprint_system.extract_narrative_fingerprint(payload.content)
    
    # 2. 和专业评价子库比对
    evaluation = await fingerprint_system.evaluate_professional(fingerprint)
    return evaluation

@router.post("/analyze_track")
async def analyze_track(payload: ScriptPayload):
    fingerprint = await fingerprint_system.extract_narrative_fingerprint(payload.content)
    
    # 3. 和赛道适配子库比对
    track_analysis = await fingerprint_system.analyze_track(fingerprint, payload.target_track)
    return track_analysis

@router.post("/copyright_proof")
async def copyright_proof(payload: ScriptPayload):
    # 对接开源免费的区块链存证接口（逻辑Mock），将唯一叙事指纹上链存证
    fingerprint = await fingerprint_system.extract_narrative_fingerprint(payload.content)
    
    # 生成指纹哈希
    fp_hash = hashlib.sha256(str(fingerprint).encode()).hexdigest()
    
    # 模拟上链存证
    timestamp = datetime.now().isoformat()
    certificate_id = f"CERT-BLOCK-{random.randint(100000, 999999)}"
    tx_hash = f"0x{hashlib.sha256(str(random.random()).encode()).hexdigest()}"
    
    return {
        "status": "success",
        "certificate_id": certificate_id,
        "tx_hash": tx_hash,
        "timestamp": timestamp,
        "fingerprint_hash": fp_hash,
        "watermark_data": f"NARRATIVE_FP:{fp_hash[:16]}"
    }

