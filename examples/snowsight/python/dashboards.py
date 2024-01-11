from auth import creds
import snowflake.connector
import os

ctx = snowflake.connector.connect(
    user=creds.username,
    password=creds.password,
    account=creds.account,
    role=os.environ["ROLE_CON"],
    warehouse=os.environ["WARHOUSE_CON"],
)

dashboard_list = []
cs = ctx.cursor()

try:
    dashboard_obj = os.environ["TABLE_OBJ"]
    query = (
        f'select "Dashboard Link" from {dashboard_obj} where "Status"=\'Operational\';'
    )

    cs.execute(query)
    res = cs.fetchall()

    for i in range(0, len(res)):
        id_val = res[i][0]
        if id_val.endswith("#query"):
            pass
        else:
            id_val = str(id_val)
            id_val = id_val[::-1]
            b = id_val.find("-")
            id_val = id_val[0:b]
            id_val = id_val[::-1]
            dashboard_list.append(id_val[1:])
finally:
    cs.close()
ctx.close()
