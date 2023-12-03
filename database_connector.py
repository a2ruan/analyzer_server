# Connect to postgresql database for row and column i/o
from time import time
from sys import getsizeof
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import create_engine, text, inspect
import asyncio
from datetime import datetime

class database_connector:
    def __init__(self):
        self.db_port = 5432
        self.db_host = "PLACEHOLDER"
        self.db_name = 'PLACEHOLDER'
        self.db_user_name = "PLACEHOLDER"
        self.db_pwd = "PLACEHOLDER"

    def get_tables(self, table="department_name_test"):
        output = {}
        try:
            DATABASE_URI = f"postgresql+psycopg2://{self.db_user_name}:{self.db_pwd}@{self.db_host}:{self.db_port}/{self.db_name}"
            engine = create_engine(DATABASE_URI)
            insp = inspect(engine)
            print(insp.get_table_names())

            return output
        except Exception as fetch_data_exception:
            print(fetch_data_exception)
            return {}

    def fetch_data(self, table="department_name_test", columns=["id","test_case","test_log","report","uuid","start_time","current_time","status","report_hash"]):
        output = {}
        try:
            DATABASE_URI = f"postgresql+psycopg2://{self.db_user_name}:{self.db_pwd}@{self.db_host}:{self.db_port}/{self.db_name}"
            engine = create_engine(DATABASE_URI)
            with engine.connect() as connection:
                column_text = ""
                for column in columns: column_text += column + ","
                search_str = "SELECT " + f"{column_text[:-1] or '*'}" + " FROM \"" + table + "\""
                query = connection.execute(text(search_str))
                for i,row in enumerate(query): 
                    output[i] = row._asdict()
            return output
        except Exception as fetch_data_exception:
            print(fetch_data_exception)
            return {}

    def write_to_table_by_uuid(self, table, uuid, payload={},column_name=None, value=None):
        # If uuid doesn't exist, will make a new row  -- this is done by default
        # If row with uuid exists, will edit that row -- this is done by default

        # Custom section for accepting POST requests
        values_dict = {}
        if column_name == None and value == None and payload != {}:
            values_dict = payload
        DATABASE_URI = f"postgresql+psycopg2://{self.db_user_name}:{self.db_pwd}@{self.db_host}:{self.db_port}/{self.db_name}"
        engine = create_engine(DATABASE_URI)
        with engine.connect() as conn:
            
            # Search for first row with given uuid.
            max_rows = 0
            row_id_list = []
            command = f"SELECT * FROM {table} WHERE uuid='{uuid}'"
            try:
                print(command)
                query = conn.execute(text(command))
                for row in query:
                    max_rows += 1
                    print(row._asdict())
                    row_id = print(row._asdict()['id'])
                    row_id_list.append(row_id)
            except Exception as e:
                print(e)
                print(f"Cannot find row with uuid={uuid}")
            
            # If row count is 0, then add a row
            now = datetime.now()
            print(max_rows)
            if max_rows == 0:
                try:
                    command = f"""INSERT INTO {table} (uuid) VALUES ('{uuid}')"""
                    write_query = conn.execute(text(command))
                except:
                    print("No column uuid in table schema.  Please add uuid column to table.")
                
                try:
                    command = f"""UPDATE {table} SET "start_time"='{datetime.now()}',"current_time"='{datetime.now()}' WHERE uuid='{uuid}'"""
                    write_query = conn.execute(text(command))
                    print(write_query)
                except:
                    print("No start_time column.  Optional.")
                
            else:
                
                # Update the time if column exists
                try: # EDIT: DO NOT UPDATE TIME COLUMN IF EXISTS
                    pass
                    #command = f"""UPDATE {table} SET "current_time"='{datetime.now()}' WHERE uuid='{uuid}'"""
                    #write_query = engine.execute(text(command))
                except:
                    pass

            # Write value to column based on table name and uuid (which defines the row)
            try:
                
                if column_name == None and value == None and payload != {}:
                    # If POST method is used, update all columns at once
                    value_write_headers = ""

                    for key in values_dict:
                        value_write_headers += f"{key}='{str(values_dict[key])}',"
                    # Remove last comma
                    value_write_headers = value_write_headers.rstrip(',')
                    print(value_write_headers)
                    command = f"UPDATE {table} SET {value_write_headers} WHERE uuid='{uuid}'"    
                else: 
                    command = f"UPDATE {table} SET {column_name}='{value}' WHERE uuid='{uuid}'"    
                print(command)
                write_query = conn.execute(text(command))
                conn.commit()
                print("done writing to db")
            except Exception as e:
                print(e)
                return False
        return True

if __name__ == "__main__":
    
    db_connector = database_connector()
    output_dict = db_connector.fetch_data(table="department_name_test", columns=["id","test_case","test_log","uuid","start_time","current_time","status"])
    assert output_dict != {},"Unit test failed, unable to fetch data from database"
    print(str(getsizeof(output_dict)/1000000) + " MB")

    db_connector.get_tables()
    """
    db_connector = database_connector()
    db_connector.write_to_table_by_uuid(table="department_name_test",uuid="a678c7c8-2a28-441e-97da-003fb7258100",payload={
        "report":"ok"})
    """


