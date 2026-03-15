import json
from datetime import timedelta, datetime
import random

import asyncpg
from config_data.config import Config, load_config
from logger.logger_config import get_logger

logger = get_logger(__name__)

config: Config = load_config()


class DBGateway:
    def __init__(self):
        self.user = config.db_connector.db_user
        self.password = config.db_connector.db_pass
        self.database = config.db_connector.db_name
        self.host = config.db_connector.db_host
        self.port = config.db_connector.db_port
        self.conn = None

    async def connect(self):
        if self.conn is None:
            self.conn = await asyncpg.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                host=self.host,
                port=self.port,
            )
        return self.conn

    async def get_db_schema(self):
        conn = await self.connect()
        sql_request = """
            SELECT 
                t.table_name,
                json_agg(
                    json_build_object(
                    'column_name', c.column_name,
                    'data_type', c.data_type,
                    'is_nullable', c.is_nullable,
                    'column_default', c.column_default
                    ) ORDER BY c.ordinal_position
                ) as columns
            FROM information_schema.tables t
            JOIN information_schema.columns c
                ON c.table_schema = t.table_schema
                AND c.table_name = t.table_name
            WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name
            ORDER BY t.table_name;
        """
        rows = await conn.fetch(sql_request)
        result = [dict(row) for row in rows]

        return json.dumps(result, default=str, ensure_ascii=False)

    async def get_sql_request_result(self, sql_request_from_ai: str):
        conn = await self.connect()
        rows = await conn.fetch(sql_request_from_ai)
        result = [dict(row) for row in rows]
        return json.dumps(result, default=str, ensure_ascii=False)

    async def sql_validate(self, sql_request_from_ai: str):
        conn = await self.connect()
        try:
            await conn.execute(f"EXPLAIN {sql_request_from_ai}")
            return True, None
        except asyncpg.PostgresError as e:
            return False, f"Произошла ошибка {str(e)}"

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def create_fake_database(self):
        """Создание фейковой базы данных"""

        conn = await self.connect()
        try:
            # Таблица departments
            await conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS departments (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        location VARCHAR(100),
                        budget DECIMAL(15, 2),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            )

            # Таблица employees
            await conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        first_name VARCHAR(50) NOT NULL,
                        last_name VARCHAR(50) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        phone VARCHAR(20),
                        hire_date DATE NOT NULL,
                        salary DECIMAL(10, 2),
                        department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                        manager_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """
            )

            # Таблица projects
            await conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS projects (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        start_date DATE,
                        end_date DATE,
                        budget DECIMAL(15, 2),
                        department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
                        status VARCHAR(20) DEFAULT 'active'
                    )
                """
            )

            # Таблица employee_projects
            await conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS employee_projects (
                        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
                        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                        role VARCHAR(100),
                        hours_worked DECIMAL(10, 2) DEFAULT 0,
                        joined_date DATE DEFAULT CURRENT_DATE,
                        PRIMARY KEY (employee_id, project_id)
                    )
                """
            )

            # Таблица tasks
            await conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                        assigned_to INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                        created_by INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                        priority INTEGER DEFAULT 1,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        due_date DATE,
                        completed_at TIMESTAMP
                    )
                """
            )

        except asyncpg.PostgresError as e:
            logger.error(str(e))

    async def trunc_db_values(self):
        """Очистка существующих данных"""

        conn = await self.connect()
        try:
            await conn.execute("TRUNCATE TABLE tasks CASCADE")
            await conn.execute("TRUNCATE TABLE employee_projects CASCADE")
            await conn.execute("TRUNCATE TABLE projects CASCADE")
            await conn.execute("TRUNCATE TABLE employees CASCADE")
            await conn.execute("TRUNCATE TABLE departments CASCADE")

        except asyncpg.PostgresError as e:
            logger.error(str(e))

    async def add_test_data(self):
        """Добавление тестовых данных"""

        conn = await self.connect()
        try:
            # Отделы
            departments = [
                ('IT', 'Москва', 5000000),
                ('HR', 'Санкт-Петербург', 1000000),
                ('Sales', 'Москва', 3000000),
                ('Marketing', 'Казань', 2000000),
                ('Finance', 'Новосибирск', 2500000),
                ('R&D', 'Сколково', 8000000)
            ]

            for dept in departments:
                await conn.execute(
                    "INSERT INTO departments (name, location, budget) VALUES ($1, $2, $3)",
                    dept[0], dept[1], dept[2]
                )

            # Получаем ID отделов
            dept_ids = await conn.fetch("SELECT id FROM departments")
            dept_ids = [d['id'] for d in dept_ids]

            # Имена и фамилии
            first_names = ['Александр', 'Мария', 'Дмитрий', 'Анна', 'Сергей', 'Елена',
                           'Андрей', 'Ольга', 'Михаил', 'Татьяна', 'Иван', 'Наталья']
            last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов',
                          'Попов', 'Лебедев', 'Козлов', 'Новиков', 'Морозов']

            # Генерация сотрудников
            employees = []
            for i in range(50):
                first = random.choice(first_names)
                last = random.choice(last_names)
                email = f"{first.lower()}.{last.lower()}{random.randint(1, 999)}@company.ru"
                phone = f"+7 {random.randint(900, 999)}-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
                hire_date = datetime.now() - timedelta(days=random.randint(30, 2000))
                salary = random.randint(50000, 300000)
                dept_id = random.choice(dept_ids)

                emp_id = await conn.fetchval("""
                    INSERT INTO employees (first_name, last_name, email, phone, hire_date, salary, department_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
                """, first, last, email, phone, hire_date, salary, dept_id)

                employees.append(emp_id)

            # Назначаем менеджеров
            managers = random.sample(employees, min(10, len(employees)))
            for emp_id in employees[10:]:
                await conn.execute(
                    "UPDATE employees SET manager_id = $1 WHERE id = $2",
                    random.choice(managers), emp_id
                )

            # Проекты
            project_names = [
                'Разработка CRM', 'Внедрение ERP', 'Маркетинговая кампания 2025',
                'Оптимизация продаж', 'Исследование рынка', 'Мобильное приложение',
                'Облачная инфраструктура', 'Обучение персонала', 'Автоматизация отчетности',
                'Анализ данных', 'Разработка сайта', 'Тестирование ПО'
            ]

            projects = []
            for name in project_names:
                start = datetime.now() - timedelta(days=random.randint(0, 365))
                end = start + timedelta(days=random.randint(90, 365)) if random.random() > 0.3 else None
                budget = random.randint(100000, 5000000)
                dept_id = random.choice(dept_ids)
                status = random.choice(['active', 'completed', 'on_hold'])

                proj_id = await conn.fetchval("""
                    INSERT INTO projects (name, description, start_date, end_date, budget, department_id, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
                """, name, f'Описание проекта {name}', start, end, budget, dept_id, status)

                projects.append(proj_id)

            # Назначение сотрудников на проекты
            roles = ['Разработчик', 'Аналитик', 'Тестировщик', 'Менеджер', 'Дизайнер', 'DevOps']
            for project_id in projects:
                for emp_id in random.sample(employees, random.randint(3, 15)):
                    role = random.choice(roles)
                    hours = random.randint(10, 500)
                    joined = datetime.now() - timedelta(days=random.randint(1, 300))

                    await conn.execute("""
                        INSERT INTO employee_projects (employee_id, project_id, role, hours_worked, joined_date)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (employee_id, project_id) DO NOTHING
                    """, emp_id, project_id, role, hours, joined)

            # Задачи
            task_titles = [
                'Разработать API', 'Написать тесты', 'Создать дизайн', 'Провести анализ',
                'Подготовить отчет', 'Обновить документацию', 'Исправить баги',
                'Провести встречу', 'Собрать требования', 'Развернуть сервер',
                'Написать документацию', 'Провести код-ревью', 'Оптимизировать запросы'
            ]
            task_statuses = ['pending', 'in_progress', 'review', 'completed']

            for project_id in projects:
                # Получаем сотрудников на проекте
                project_employees = await conn.fetch(
                    "SELECT employee_id FROM employee_projects WHERE project_id = $1",
                    project_id
                )
                project_employees = [pe['employee_id'] for pe in project_employees]

                for _ in range(random.randint(5, 15)):
                    title = random.choice(task_titles)
                    status = random.choice(task_statuses)
                    priority = random.randint(1, 5)

                    assigned = random.choice(project_employees) if project_employees else None
                    created = random.choice(employees)

                    created_at = datetime.now() - timedelta(days=random.randint(0, 100))
                    due = created_at + timedelta(days=random.randint(1, 30))

                    completed_at = due if status == 'completed' and random.random() > 0.5 else None

                    await conn.execute("""
                        INSERT INTO tasks 
                        (title, description, project_id, assigned_to, created_by, 
                         priority, status, created_at, due_date, completed_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """, title, f'Описание задачи: {title}', project_id,
                                     assigned, created, priority, status, created_at, due, completed_at)

            logger.info("✅ Тестовые данные добавлены")

        except asyncpg.PostgresError as e:
            logger.error(str(e))

    async def get_test_data(self):
        """Получение статистики тестовых данных"""

        conn = await self.connect()
        try:
            dept_count = await conn.fetchval("SELECT COUNT(*) FROM departments")
            emp_count = await conn.fetchval("SELECT COUNT(*) FROM employees")
            proj_count = await conn.fetchval("SELECT COUNT(*) FROM projects")
            tasks_count = await conn.fetchval("SELECT COUNT(*) FROM tasks")

            return dept_count, emp_count, proj_count, tasks_count

        except asyncpg.PostgresError as e:
            logger.error(str(e))

    async def try_get_test_data(self):
        """Получение тестовых данных по тестовому запросу"""

        conn = await self.connect()
        try:
            employees_sample = await conn.fetch(
                """
                    SELECT e.id, e.first_name, e.last_name, d.name as department
                    FROM employees e
                    LEFT JOIN departments d ON e.department_id = d.id
                    LIMIT 5
                """
            )
            return employees_sample

        except asyncpg.PostgresError as e:
            logger.error(str(e))
