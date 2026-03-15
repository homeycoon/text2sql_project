import re

from .database import DBGateway


class SQLValidator:
    def __init__(self):
        self.db = DBGateway()

    async def __call__(self, sql_request_from_ai):
        try:
            dangerous = ['drop', 'truncate', 'delete', 'update', 'insert',
                         'alter', 'create', 'grant', 'revoke', 'into']
            query_lower = sql_request_from_ai.lower()
            for word in dangerous:
                if re.search(rf'\b{word}\b', query_lower):
                    return False, f"Встретилось стоп-слово {word.upper()}"

            if 'select' not in query_lower:
                return False, f"Запрос не содержит SELECT"

            valid_result, comment = await self.db.sql_validate(sql_request_from_ai)

            return valid_result, comment
        finally:
            await self.db.close()
