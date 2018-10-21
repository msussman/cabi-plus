import sys
sys.path.append("..")
import pandas as pd
import numpy as np
import util_functions as uf
import json
import requests
from datetime import date
from geopy.distance import great_circle


def query(con):
    # queries bikeshare db
    return pd.read_sql("""WITH 
                        station_coords AS (SELECT short_name,
                                name,
                                lat, 
                                lon				      
                                FROM cabi_stations),
                        cabi_plus AS (SELECT *
                                FROM cabi_trips
                                WHERE left(bike_number, 1) not in ('?', 'w', 'W', 'Z')),
                        cabi_classic AS (SELECT *
                                    FROM cabi_trips
                                    WHERE left(bike_number, 1) in ('?', 'w', 'W', 'Z'))
                        
                        /* CaBi Plus Top 10 Stations*/
                        (SELECT DISTINCT
                        'CaBi Plus' as bike_type, 
                        start_station,
                        end_station,
                        start_coords.name AS start_name,
                        start_coords.lat AS start_lat,
                        start_coords.lon AS start_lon,
                        end_coords.name AS end_name,
                        end_coords.lat AS end_lat,
                        end_coords.lon AS end_lon,
                        count(*) AS total_trips
                        FROM cabi_plus as cabi_plus
                        LEFT JOIN station_coords as start_coords
                        ON cabi_plus.start_station = start_coords.short_name
                        LEFT JOIN station_coords as end_coords
                        ON cabi_plus.end_station = end_coords.short_name
                        WHERE start_date::date >= '2018-09-05'
                        AND member_type = 'Member'
                        AND end_date > start_date
                        GROUP by 1, 2, 3, 4, 5, 6, 7, 8, 9
                        ORDER by 10 DESC
                        LIMIT 10)
                        UNION
                        /* CaBi Classic Top 10 Stations*/
                        (SELECT DISTINCT
                        'CaBi Classic' as bike_type, 
                        start_station,
                        end_station,
                        start_coords.name AS start_name,
                        start_coords.lat AS start_lat,
                        start_coords.lon AS start_lon,
                        end_coords.name AS end_name,
                        end_coords.lat AS end_lat,
                        end_coords.lon AS end_lon,
                        count(*) AS total_trips
                        FROM cabi_classic as cabi_classic
                        LEFT JOIN station_coords as start_coords
                        ON cabi_classic.start_station = start_coords.short_name
                        LEFT JOIN station_coords as end_coords
                        ON cabi_classic.end_station = end_coords.short_name
                        WHERE start_date::date >= '2018-09-05'
                        AND member_type = 'Member'
                        AND end_date > start_date
                        GROUP by 1, 2, 3, 4, 5, 6, 7, 8, 9
                        ORDER by 10 DESC
                        LIMIT 10)
                        ORDER by bike_type, total_trips DESC;
                        """, con=con)


if __name__ == "__main__":

    # Generating Data
    conn, cur = uf.local_connect()
    # Return query from db into dataframe
    df = query(con=conn)
    # Calculate distance between geo-coordinates
    df['distance'] = df.apply(lambda x: great_circle((x['start_lat'], x['start_lon']), 
                                                               (x['end_lat'], x['end_lon'])).miles, axis = 1)
    df.to_csv('cabi_top10_stations.csv')                                                           
    