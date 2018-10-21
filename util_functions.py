import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

def set_env_path():
    # set the environment path
    env_path = '../.env'
    load_dotenv(dotenv_path=env_path)

def local_load(df_name, tbl_name, cur):
    # Load dataframe of data to AWS table
    with open(df_name + ".csv", 'r') as f:
        # Skip the header row.
        next(f)
        cur.copy_from(f, tbl_name, sep='|')
    print("{} has been loaded to the {} database".format(df_name, tbl_name))


def local_connect():
    '''
    Establishes connection to local postgres database
    used for further work with DDOT
    '''
    host = "localhost"
    database = "bikeshare"
    user = "postgres"
    conn = psycopg2.connect(host=host, user=user,
                            database=database)
    cur = conn.cursor()
    return conn, cur