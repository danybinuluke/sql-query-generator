import re
from pathlib import Path

def parse_schema(file_path):
    with open(file_path,'r') as f:
        sql=f.read()
    tables={}
    pattern=r"CREATE TABLE\s+`?(\w+)`?\s*\((.*?)\)\s*ENGINE=.*?;"
    matches=re.findall(
        pattern,
        sql,
        re.DOTALL | re.IGNORECASE
    )
    for table,columns in matches:
        cols=[]
        for col in columns.splitlines():
            col=col.strip().rstrip(",")
            if not col.startswith("`"):
                continue
            col_name=col.split("`", 2)[1]
            cols.append(col_name)
        tables[table]=cols
    return tables

if __name__ == "__main__":
    schema_path = Path(__file__).with_name("schema.sql")
    schema = parse_schema(schema_path)
    print(schema)