from fastapi import FastAPI, Body, Depends, HTTPException, Request, status
from typing import List
import schemas, models
from db import engine, get_db
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
import helpers
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import pdb

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Возвращает ошибку при плохом вводе
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": "Validation error"}),
    )


# Добавляет объект в базу данных
@app.post('/imports')
def import_items(items: List[schemas.SystemItemImport], updateDate: datetime = Body(), db: Session = Depends(get_db)):
    for item in items:
        if item.parentId == item.id or (item.parentId != None and db.query(models.SystemItem).filter(
                models.SystemItem.id == item.parentId).first() is None):  # Если id и parentId одинаковы, или parentId нет в базе данных - выходит ошибка
            raise HTTPException(status_code=400, detail='Validation error')
        new_item = db.query(models.SystemItem).filter(models.SystemItem.id == item.id).first()
        if new_item:  # Если объект уже есть в базе, то обновляем
            helpers.calculate_size(new_item, db, -new_item.size)  # пересчитываем размер
            if new_item.type != item.type:
                raise HTTPException(status_code=400, detail='Validation error')
            new_item.date = updateDate  #обновляем данные
            new_item.size = item.size
            new_item.url = item.url
            new_item.parentId = item.parentId

        else:  # Если не найден, создаём новый объект
            new_item = models.SystemItem(id=item.id, type=item.type, url=item.url, size=item.size,
                                         parentId=item.parentId, date=updateDate)
            db.add(new_item)

        helpers.calculate_size(new_item, db, item.size)  # увеличиваем размер родителей
        helpers.update_date(new_item, db, updateDate)  #обновляем историю для всех родителей
        new_history = models.SystemItemHistory(item_id=item.id, date=updateDate)  # добавляем изменение объекта в его историю
        db.add(new_history)
        db.commit()


# Удаление объекта
@app.delete('/delete/{id}')
def delete_item(id: str, date: datetime, db: Session = Depends(get_db)):
    item = db.query(models.SystemItem).filter(models.SystemItem.id == id).first()
    if item:  # Если объект найден
        helpers.update_date(item, db, date)  # дата изменений обновляется
        helpers.calculate_size(item, db, -item.size)  # размер внешних папок уменьшается
        helpers.deleter(item, db)  # все внутренние объекты удаляются

        db.query(models.SystemItemHistory).filter(models.SystemItemHistory.item_id == item.id).delete()  # история изменений объекта удаляется
        db.query(models.SystemItem).filter(models.SystemItem.id == id).delete()  # удаляется сам объект
        db.commit()
        return 'Done'
    else:
        raise HTTPException(status_code=404, detail='Item not found')  # Ошибка, если объект не найден


# Вывод объекта, если он найден, иначе ошибка
@app.get('/nodes/{id}')
def get_item(id: str, db: Session = Depends(get_db)):  # Не смогла подобрать response модель, проблема описана в файле explanation.md
    item = db.query(models.SystemItem).filter(models.SystemItem.id == id).first()
    if item:
        helpers.output(item)  # Используем рекурсивное подтягивание всех детей, т.к. joinedload работает только для первого потомства
        return item
    else:
        raise HTTPException(status_code=404, detail='Item not found')


# Вывод всех объектов, которые быи изменены за последние 24 часа
@app.get('/updates', response_model=List[schemas.SystemItemImport])
def get_updates(date: datetime, db: Session = Depends(get_db)):
    item = db.query(models.SystemItem).filter(models.SystemItem.date <= date)
    item = item.filter(models.SystemItem.date > date - timedelta(hours=24))
    return item.all()


#Вывод всех объектов, которые были изменены в указанный промежуток времени
@app.get('/node/{id}/history', response_model=List[schemas.Udpates])
def get_history(id: str, dateStart: datetime, dateEnd: datetime, db: Session = Depends(get_db)):
    item = db.query(models.SystemItemHistory).filter(models.SystemItemHistory.item_id == id)
    if item:
        item = item.filter(models.SystemItemHistory.date >= dateStart)
        item = item.filter(models.SystemItemHistory.date < dateEnd)
        return item.all()
    else:
        raise HTTPException(status_code=404, detail='Item not found')
