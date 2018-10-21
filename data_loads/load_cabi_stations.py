import sys
sys.path.append("..")
import requests
import pandas as pd
import numpy as np
import util_functions as uf
import os


def pull_station_info():
    # Load CaBI region information from API
    station_url = "https://gbfs.capitalbikeshare.com/gbfs/en/station_information.json"
    stations = requests.get(station_url).json()
    station_df = pd.DataFrame(stations['data']['stations'])
    return station_df


def create_cabi_stations(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS cabi_stations;
    CREATE TABLE cabi_stations(
        capacity integer,
        lat numeric,
        lon numeric,
        name varchar(200),
        region_id integer,
        short_name varchar(20),
        station_id integer PRIMARY KEY)
            """)


if __name__ == "__main__":
    # Connect to db
    conn, cur = uf.local_connect()
    # Pull CaBi System Regions
    station_df = pull_station_info()
    # Default any missing region ids to DC (only example as of 2/21 is new station at Anacostia Park)
    station_df['region_id'] = np.where(station_df['region_id'].isnull(), 42, station_df['region_id'])
    station_df['region_id'] = station_df['region_id'].astype(int)
    keep_cols = ['capacity', 'lat', 'lon', 'name', 'region_id', 'short_name', 'station_id' ]
    # Output dataframe as CSV
    outname = "CaBi_Stations"
    station_df[keep_cols].to_csv(outname + ".csv", index=False, sep='|')
    # Create Database
    create_cabi_stations(cur)
    # Load to Database
    uf.local_load(outname, "cabi_stations", cur)
    # Commit changes to database
    conn.commit()
