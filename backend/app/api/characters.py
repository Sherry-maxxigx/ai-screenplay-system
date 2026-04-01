from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, Character
from pydantic import BaseModel
from typing import List

router = APIRouter()

# 人物模型
class CharacterBase(BaseModel):
    name: str
    description: str = None
    traits: str = None  # JSON格式存储人物特质

class CharacterCreate(CharacterBase):
    project_id: int

class CharacterUpdate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    id: int
    project_id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

# 创建人物
@router.post("/", response_model=CharacterResponse)
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    db_character = Character(
        name=character.name,
        project_id=character.project_id,
        description=character.description,
        traits=character.traits
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

# 获取项目的人物列表
@router.get("/project/{project_id}", response_model=List[CharacterResponse])
def get_project_characters(project_id: int, db: Session = Depends(get_db)):
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    return characters

# 获取单个人物
@router.get("/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="人物不存在")
    return character

# 更新人物
@router.put("/{character_id}", response_model=CharacterResponse)
def update_character(character_id: int, character: CharacterUpdate, db: Session = Depends(get_db)):
    db_character = db.query(Character).filter(Character.id == character_id).first()
    if db_character is None:
        raise HTTPException(status_code=404, detail="人物不存在")
    
    db_character.name = character.name
    db_character.description = character.description
    db_character.traits = character.traits
    
    db.commit()
    db.refresh(db_character)
    return db_character

# 删除人物
@router.delete("/{character_id}")
def delete_character(character_id: int, db: Session = Depends(get_db)):
    db_character = db.query(Character).filter(Character.id == character_id).first()
    if db_character is None:
        raise HTTPException(status_code=404, detail="人物不存在")
    
    db.delete(db_character)
    db.commit()
    return {"message": "人物删除成功"}