import asyncio

from database import DBGateway
from logger.logger_config import get_logger

logger = get_logger(__name__)


async def load_data_to_db():
    """Основная функция"""
    db = DBGateway()

    try:
        await db.create_fake_database()
        await db.trunc_db_values()
        await db.add_test_data()

        # Проверка количества записей
        dept_count, emp_count, proj_count, tasks_count = await db.get_test_data()

        logger.info(
            "Статистика базы данных:"
            f"  Отделы: {dept_count}"
            f"  Сотрудники: {emp_count}"
            f"  Проекты: {proj_count}"
            f"  Задачи: {tasks_count}"
        )

        employees_sample = await db.try_get_test_data()
        for emp in employees_sample:
            logger.info(f"  {emp['first_name']} {emp['last_name']} - {emp['department']}")

    except Exception as e:
        logger.error(str(e))

if __name__ == "__main__":
    asyncio.run(load_data_to_db())
