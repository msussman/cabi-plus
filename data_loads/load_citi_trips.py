import pandas as pd
import os
import sys
sys.path.append("..")
import util_functions as uf


def trips_to_df(citi_trip_dir, year):
    # Loop through CSVs of Trip Data
    csv_list = [
        f for f in sorted(os.listdir(citi_trip_dir)) if (f.endswith('.csv')) 
                                                         & (str(year) in f)
    ]
    for csv in csv_list:
        csv_name = csv.replace('.csv', '')
        print("{} has started processing".format(csv_name))
        # Load original CSV as dataframe
        trip_df = pd.read_csv(os.path.join(
            citi_trip_dir, csv_name + '.csv'))

        keep_cols = ['tripduration', 'starttime', 'stoptime', 'start station id',
                     'end station id', 'bikeid', 'usertype']        
        trip_df = trip_df[keep_cols].copy()
            
            #.drop(
             #   ['Start station', 'End station'], axis=1)
        trip_df.columns = [
            'duration', 'start_date', 'end_date', 'start_station',
            'end_station', 'bike_number', 'member_type'
        ]

        trip_df['start_date'] = pd.to_datetime(trip_df['start_date'])
        trip_df['end_date'] = pd.to_datetime(trip_df['end_date'])
        # Output dataframe as CSV
        outname = "Citi_Trip_Data"
        trip_df.to_csv(outname + ".csv", index=False, sep='|')
        # Load to Database
        uf.local_load(outname, "citi_trips", cur)
        # Commit changes to database
        conn.commit()


def create_citi_trips(cur):
    # This script creates the CaBi System AWS table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS citi_trips(
        duration integer,
        start_date timestamp,
        end_date timestamp,
        start_station varchar(20),
        end_station varchar(20),
        bike_number varchar(30),
        member_type varchar(20)
    )
            """)


if __name__ == "__main__":

    # Connect to AWS
    conn, cur = uf.local_connect()
    # Create Table
    create_citi_trips(cur)

    # Loop through all CSVs in cabi trip data folder
    citi_trip_dir = '../citibike_data'
    for year in [2013, 2014, 2015, 2016, 2017, 2018]:
        # Convert trip data from CSV to dataframe
        trips_to_df(citi_trip_dir, year)
    