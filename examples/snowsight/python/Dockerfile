FROM ubuntu

RUN apt-get update && apt-get install -y wget unzip python3.6 python3-pip && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install -r https://raw.githubusercontent.com/snowflakedb/snowflake-connector-python/v2.3.8/tested_requirements/requirements_36.reqs

RUN pip install snowflake-connector-python==2.3.8

COPY snowsight_basic.py auth.py dashboards.py ./

CMD python3 snowsight_basic.py
