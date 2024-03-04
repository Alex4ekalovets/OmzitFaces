import io
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, DateTime, String, URL, LargeBinary, func
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from PIL import Image

from settings import DETECT_LITE_DB, DETECT_PG_DB
from utils.b2p import get_scud_employees_data

logger = logging.getLogger("logger")

connection_url = URL.create(**DETECT_PG_DB)

# engine = create_engine(f'sqlite:///{DETECT_LITE_DB}', echo=True)
engine = create_engine(connection_url)


class Base(DeclarativeBase):
    pass


class EmployeePhoto(Base):
    """Модель с фотографиями сотрудников"""
    __tablename__ = 'employee'

    id: Mapped[int] = mapped_column(primary_key=True)
    scud_id: Mapped[Optional[int]]
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    photo: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    is_unknown: Mapped[bool] = mapped_column(default=False)


class Detection(Base):
    """Модель факта обнаружения"""
    __tablename__ = 'detection'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    datetime: Mapped[datetime] = mapped_column(DateTime(), default=func.now())
    photo: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    is_unknown: Mapped[bool] = mapped_column(default=False)


Base.metadata.create_all(engine)


def create(model, **kwargs) -> None:
    with Session(autoflush=False, bind=engine) as db:
        record = model(**kwargs)
        db.add(record)
        try:
            db.commit()
        except Exception as ex:
            logger.exception(ex)


def bulk_create(model, records) -> None:
    with Session(autoflush=False, bind=engine) as db:
        add_records = []
        for record in records:
            add_records.append(model(**record))
        db.add_all(add_records)
        try:
            db.commit()
        except Exception as ex:
            logger.exception(ex)


def sync_db_with_scud():
    scud_employees = get_scud_employees_data()
    if scud_employees:
        scud_ids = {emp['scud_id'] for emp in scud_employees}
        with Session(autoflush=False, bind=engine) as db:
            employees = db.query(EmployeePhoto).filter(EmployeePhoto.scud_id is not None)
            ids = {employee.scud_id for employee in employees}
            deleted_ids = list(ids - scud_ids)
            if deleted_ids:
                employees.filter(EmployeePhoto.scud_id.in_(deleted_ids)).delete()
                db.commit()
        created_ids = list(scud_ids - ids)
        if created_ids:
            created = list(filter(lambda x: x['scud_id'] in created_ids, scud_employees))
            bulk_create(EmployeePhoto, created)
        logger.info(f'Синхронизация со СКУД завершена')

        with Session(autoflush=False, bind=engine) as db:
            rows = db.query(EmployeePhoto)
            employees = {'ids': [], 'names': [], 'photos': []}
            for row in rows:
                employees['ids'].append(row.id)
                employees['names'].append(row.name)
                employees['photos'].append(row.photo)
        return employees


if __name__ == "__main__":
    with Session(autoflush=False, bind=engine) as db:
        rows = db.query(Detection).filter_by(id=1)
        for row in rows:
            image = Image.open(io.BytesIO(row.photo))
            image.show()
