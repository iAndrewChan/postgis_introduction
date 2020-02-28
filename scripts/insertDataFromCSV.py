import psycopg2
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

"""
Read Das data in CSV format and write into PostgreSQL

Look for whether the table exists in the database called 'postgres'
If the table does not exist then the table will be created and data will be inserted line by line
If the table does exist then the table will be cleared of all its data and the data will be inserted line by line

The csv data will be loaded in using pandas

Further Improvement:
Read the xlsx data into pandas and then insert into PostgreSQL without writing it to a CSV
"""

def list_version(cursor) -> None:
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print(record)

def list_cmds(cursor, qstr: str) -> None:

    query: Dict[str, str] = {
        'list db': """SELECT datname FROM pg_database
                      WHERE datistemplate=false;""",
        'list table': """SELECT table_name
                         FROM information_schema.tables
                         WHERE table_type=\'BASE TABLE\';"""
    }
    
    sql_query: Optional[str] = query.get(qstr)
    if sql_query is None:
        raise Exception("Key", qstr, "does no exist in ", query.keys())

    cursor.execute(sql_query)
    record = cursor.fetchall()
    print(record)

def fetch_cmds(cursor, qstr: str, tablename: str ='departures') -> List[Any]:

    query: Dict[str, str] = {
        'departures table exist': """SELECT tablename
                                     FROM pg_catalog.pg_tables
                                     WHERE tablename=\'{tn}\';""".format(tn=tablename)
    }
    
    sql_query: Optional[str] = query.get(qstr)
    if sql_query is None:
        raise Exception("Key", qstr, "does no exist in ", query.keys())

    cursor.execute(sql_query)
    record = cursor.fetchall()
    return record

def update_db_cmds(connection, cursor, qstr: str, tablename: str ='departures') -> None:

    query: Dict[str, str] = {
        'create table': """CREATE TABLE {tn} (
                           DepartureID INT,
                           StructureKey INT,
                           Description TEXT,
                           GridRef CHAR(14),
                           Easting INT,
                           Northing INT,
                           Lat double precision,
                           Long double precision,
                           Geom geometry);""".format(tn=tablename),
        'delete table': 'DROP TABLE {tn};'.format(tn=tablename),
        'clear table': 'TRUNCATE TABLE {tn};'.format(tn=tablename)
    }

    sql_query: Optional[str] = query.get(qstr)
    if sql_query is None:
        raise Exception("Key", qstr, "does no exist in ", query.keys())

    cursor.execute(sql_query)
    connection.commit()

def insert_data() -> None:
    """
    Insert csv data into SQL database
    """

    # SRID=4326 is the projection value, a coordinate system that uses "longitude/latitude" on the WGS84, commonly used for GPS
    insert_query: str = """INSERT INTO departures (
                                                   DepartureID, StructureKey, Description,
                                                   GridRef, Easting, Northing,
                                                   Lat, Long, Geom
                                                  )
                                                  VALUES (
                                                   %s,%s,%s,%s,%s,%s,%s,%s,
                                                   ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                                                  )"""

    df = pd.read_csv(filename, sep='|')
    data = df.values.tolist()

    lon: float
    lat: float

    for row in data:

        if len(row) != 8:
            raise Exception("length csv line does not match sql query", row, len(row))

        # TODO only a temporary solution, we will be getting rid of Easting, Northing, and Lat, Long, and GridRef
        lat = row[6]
        lon = row[7]
        row.append(lon)
        row.append(lat)
        cursor.execute(insert_query, row)

    connection.commit()

connection: Any = None
filename: str = '../src/assets/Das-data-long-lat.csv'

try:
    connection = psycopg2.connect(user = "postgres",
                                  password = "p",
                                  host = "postgres",
                                  port = "5432",
                                  database="postgres")

    cursor = connection.cursor()
    
    table_exist: List[Any] = fetch_cmds(cursor, 'departures table exist')
    if not table_exist:
        update_db_cmds(connection, cursor, 'create table')
    else:    
        update_db_cmds(connection, cursor, 'clear table')
    insert_data()

except (Exception, psycopg2.Error) as err:
    print(err)

finally:
    if(connection):
        cursor.close()
        connection.close()
