from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# На вход только два возможных значения: FOLDER или FILE
class SystemItemType(str, Enum):
    FILE = 'FILE'
    FOLDER = 'FOLDER'


# Описывается, какой тип данных ожидает каждый параметр. Иначе вызывается ошибка
class SystemItemImport(BaseModel):
    id: str
    type: SystemItemType
    url: Optional[str] = Field(default=None, max_length=255)
    parentId: Optional[str] = Field(default=None)
    size: Optional[int] = Field(default=0, ge=0)
    date: Optional[datetime]
    #children: List[SystemItemImport] - Вызывает ошибку

    class Config:
        orm_mode = True



class Udpates(BaseModel):
    item_id: str
    date: datetime

    class Config:
        orm_mode = True

