import models


# Перебиварет все внутренние объекты (детей)
def output(item):
    for child in item.children:
        output(child)


# Изменяет размер в бОльшую (при добавлении) или в меньшую(при удалении) сторону
def calculate_size(item, db, size):
    if item.parentId:
        new_item = db.query(models.SystemItem).filter(models.SystemItem.id == item.parentId).first()
        new_item.size += size

        calculate_size(new_item, db, size)


#Обновляет данные у всех внешних папок, добавляет информацию в историю обновлений
def update_date(item, db, date):
    if item.parentId:
        new_item = db.query(models.SystemItem).filter(models.SystemItem.id == item.parentId).first()
        new_item.date = date
        new_history = models.SystemItemHistory(item_id=new_item.id, date=date)
        db.add(new_history)

        update_date(new_item, db, date)


# удаляет все внутренние объекты (детей) и их истории
def deleter(item, db):
    for it in item.children:
        deleter(it, db)
        db.query(models.SystemItemHistory).filter(models.SystemItemHistory.item_id == it.id).delete()
        db.query(models.SystemItem).filter(models.SystemItem.id == it.id).delete()
