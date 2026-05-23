import re
import sqlparse


class SchemaParser:

    def __init__(self):
        pass


    def parse(self, schema_text: str):

        schema = {}

        statements = sqlparse.split(schema_text)


        for stmt in statements:

            stmt = stmt.strip()

            if not stmt.upper().startswith("CREATE TABLE"):
                continue


            table_match = re.search(
                r"CREATE TABLE\s+(\w+)",
                stmt,
                re.IGNORECASE
            )


            if not table_match:
                continue


            table_name = table_match.group(1)


            cols = re.findall(
                r"(\w+)\s+(INT|INTEGER|VARCHAR|TEXT|DATE|FLOAT|DOUBLE|BOOLEAN)",
                stmt,
                re.IGNORECASE
            )


            columns = []

            for col, dtype in cols:

                columns.append({

                    "name": col,

                    "type": dtype.upper()

                })


            schema[table_name] = {

                "columns": columns

            }


        return schema