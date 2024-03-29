import pymysql.cursors
import argparse
import os
from datetime import datetime
from flask import Flask

# 需要根据情况修改
HOST = 'tx-db.cbore8wpy3mc.us-east-2.rds.amazonaws.com'
PORT = 3306
USER = 'demo'
DBName = 'business'
# 更新meta表，获取更准确的信息。由于meta 表的信息需要手动调用analyze table命令才能更新，但是analyze 命令会对表进行上锁
# 所以不能频繁执行analyze table命令。所以需要有个间隔时间,不建议设置的太小。单位分钟
UPDATE_META_INTERVAL_MINUTES = 60
###############################################

COLUMNS = ["TABLE_NAME", "TABLE_SCHEMA", "ENGINE", "TABLE_ROWS", "AVG_ROW_LENGTH",
           "DATA_LENGTH", "MAX_DATA_LENGTH", "INDEX_LENGTH,DATA_FREE"]

KPI_NAMES = ["表名称", "数据库名称", "存储引擎", "表空间(GB)", "表空间占比(%)", "索引空间(GB)", "数据空间(GB)", "碎片率(%)",
             "表行数", "平均行长度(byte)"]

SQL = f"""
SELECT {",".join(COLUMNS)}
FROM information_schema.tables
WHERE table_schema='{DBName}'
ORDER BY data_length DESC;
"""

SQL_TOTAL_SIZE = """
SELECT
SUM(DATA_LENGTH + INDEX_LENGTH) as total_size,
SUM(DATA_FREE) as free_size
FROM information_schema.tables;
"""
SQL_TABLE_NAMES = f"""
SELECT TABLE_NAME
FROM information_schema.tables 
WHERE table_schema='{DBName}'
"""


last_update_meta = None

def get_conn():
    if 'pwd' not in os.environ:
        raise ValueError("need set the pwd paramater")
    pwd = os.environ['pwd']
    connection = pymysql.connect(host=HOST,
                                 port=PORT,
                                 user=USER,
                                 password=pwd,
                                 database=DBName,
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def fetch(sql: str, conn):
    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()
        t = cursor.fetchall()
        return t

def exec(sql: str, conn):
    with conn.cursor() as cursor:
        error = cursor.execute(sql)
        conn.commit()
        return error

def analyze(conn):
    now = datetime.now()
    global last_update_meta
    if not last_update_meta or (now - last_update_meta).total_seconds() > UPDATE_META_INTERVAL_MINUTES * 60:
        last_update_meta = now
        table_names = fetch(SQL_TABLE_NAMES, conn)
        for table_name in table_names:
            table_name_str = table_name['TABLE_NAME']
            command = f"ANALYZE TABLE {DBName}.{table_name_str}"
            print(command)
            error = exec(command, conn)
            if error:
                print(error)

def handel_summary_stat(conn):
    rows = fetch(SQL_TOTAL_SIZE, conn)
    total_size = rows[0]['total_size']
    free_size = rows[0]['free_size']
    if total_size <= 0:
        total_size = 1

    if free_size <= 0:
        free_size = 1

    return total_size, free_size


def handel_kpi():
    table_content = list()
    table_content.append(f"<html><head>数据库 {DBName} 表空间信息</head><body><table>")

    header = list()

    header.append("""<tr style="background:gray;font-size: large;font-weight: bold;">""")
    for column in KPI_NAMES:
        header.append(f"<td>{column}</td>")
    header.append("</tr>")

    table_content.append("\n".join(header))

    conn = get_conn()
    total_size, free_size = handel_summary_stat(conn)
    print(f"total table size {total_size} and total free {free_size}")

    analyze(conn)
        
    rows = fetch(SQL, conn)
    index = 0
    for row in rows:
        body = list()
        style = "style='background-color: lightblue;'" if index % 2 == 0 else "style='background-color: lightgreen;'"
        body.append(f"<tr {style}>")
        body.append(f"<td>{row['TABLE_NAME']}</td>")
        body.append(f"<td>{row['TABLE_SCHEMA']}</td>")
        body.append(f"<td>{row['ENGINE']}</td>")

        # 表空间
        table_size =round((row['DATA_LENGTH'] + row['INDEX_LENGTH']) / 1024 / 1024 / 1024, 4)
        body.append(f"<td>{table_size}</td>")
        # 表空间占比
        table_size_rato = round(((row['DATA_LENGTH'] + row['INDEX_LENGTH'])) * 100 / total_size, 4)
        body.append(f"<td>{table_size_rato}%</td>")

        index_size = round(row['INDEX_LENGTH'] / 1024 / 1024 / 1024, 4)
        body.append(f"<td>{index_size}</td>")

        data_size = round(row['DATA_LENGTH'] / 1024 / 1024 / 1024, 4)
        body.append(f"<td>{data_size}</td>")

        # 碎片率
        free_ratio = round(row['DATA_FREE'] * 100 / free_size, 4)
        body.append(f"<td>{free_ratio}</td>")
        body.append(f"<td>{row['TABLE_ROWS']}</td>")
        body.append(f"<td>{row['AVG_ROW_LENGTH']}</td>")
        body.append("</tr>")
        table_content.append("\n".join(body))
        index += 1

    table_content.append("</table></body></html>")
    return table_content


if __name__ == "__main__":
    print(os.getcwd())
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--pwd', help="数据库密码")

    parser.add_argument(
        '--mode', help="运行模式，默认是直接生成一个html单机文件，如果选择 web,则会启动一个flask轻量级web服务端")

    args = parser.parse_args()

    os.environ['pwd'] = args.pwd

    if args.mode != 'web':
        content = handel_kpi()
        with open(f"{os.getcwd()}/stat.html", mode="w") as f:
            for item in content:
                f.writelines(item)
    else:
        app = Flask(__name__)


        @app.route('/')
        def home():
            print("get kpi")
            kpi_data = handel_kpi()
            return "".join(kpi_data)


        app.run(host="0.0.0.0", port=5016)
