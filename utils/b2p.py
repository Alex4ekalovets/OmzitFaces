import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, Mapped, DeclarativeBase, mapped_column

from settings import SCUD_DB

logger = logging.getLogger("logger")

connection_url = URL.create(**SCUD_DB)
engine = create_engine(connection_url)


class Base(DeclarativeBase):
    pass


class SCUDEmployee(Base):
    """Таблица с сотрудниками из СКУД"""
    __tablename__ = 'pList'

    id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str]
    FirstName: Mapped[str]
    MidName: Mapped[str]
    Section: Mapped[int]
    Picture: Mapped[bytes]


class SCUDDivision(Base):
    """Таблица с отделами из СКУД"""
    __tablename__ = 'PDivision'

    id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str]


def get_scud_employees_data(department: str = None):
    logger.info(f'Запрос в базу СКУД...')
    metadata = Base.metadata
    try:
        with Session(autoflush=False, bind=engine) as db:
            rows = db.query(SCUDEmployee, SCUDDivision)
            rows = rows.join(SCUDDivision, SCUDEmployee.Section == SCUDDivision.id)
            if department:
                rows = rows.filter_by(Name=department)
            employees = []
            for row in rows:
                try:
                    if row[0].Picture is not None:
                        employees.append(
                            {
                                'scud_id': row[0].id,
                                'name': f'{row[0].Name} {row[0].FirstName} {row[0].MidName}',
                                'department': row[1].Name,
                                'photo': row[0].Picture
                            }
                        )
                except:
                    pass
        logger.info(f'Получено {len(employees)} фото сотрудников из базы СКУД')
        return employees
    except Exception as ex:
        logger.info(f'При запросе данных из СКУД возникло исключение: {ex}')


if __name__ == "__main__":
    get_scud_employees_data()
