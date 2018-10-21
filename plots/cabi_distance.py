import sys
sys.path.append("..")
import pandas as pd
import numpy as np
import util_functions as uf
import altair as alt
import json
import requests
from datetime import date
from geopy.distance import great_circle

alt.renderers.enable('notebook')
alt.themes.enable('opaque')


def query(con):
    # queries bikeshare db
    return pd.read_sql("""/* CaBi Station Coordinates*/
                            WITH 
                            station_coords AS (SELECT short_name, 
                                            lat, 
                                            lon				      
                                            FROM cabi_stations)


                            SELECT
                            start_date::date as date,
                            CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                                THEN 'CaBi Classic' 
                                ELSE 'CaBi Plus' END as "CaBi Bike Type",
                            start_station,
                            start_coords.lat as start_lat,
                            start_coords.lon as start_lon,
                            end_station,
                            end_coords.lat as end_lat,
                            end_coords.lon as end_lon,
                            end_date - start_date as total_trip_dur
                            FROM cabi_trips as cabi_trips
                            /* JOIN on start station lat, lon */
                            LEFT JOIN station_coords as start_coords
                            ON cabi_trips.start_station = start_coords.short_name
                            /* JOIN on end station lat, lon */
                            LEFT JOIN station_coords as end_coords
                            ON cabi_trips.end_station = end_coords.short_name

                            WHERE start_date::date >= '2018-09-05'
                            AND end_date > start_date
                            AND member_type = 'Member'
                            ;
                        """, con=con)


if __name__ == "__main__":

    # Generating Data
    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = query(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    # Convert timedelta to float of minutes
    df['Trip Duration (hours)'] = df['total_trip_dur'] / np.timedelta64(1, 'h')
    # Calculate distance between coordinates
    df['distance'] = df.apply(lambda x: great_circle((x['start_lat'], x['start_lon']), 
                                                               (x['end_lat'], x['end_lon'])).miles, axis = 1)
    # MPH
    df['mph'] = df['distance'] / df['Trip Duration (hours)'] 
   # Average Distance by CaBi/CaBi Plus    
    print(df[df['distance'] > 0].groupby('CaBi Bike Type')['distance'].mean())
    
    # Average MPH by CaBi/CaBi Plus
    print(df[df['distance'] > 0].groupby('CaBi Bike Type')['mph'].mean())

    # Average distance by day
    dist_chart_cols = ['distance', 'date', 'CaBi Bike Type']
    dist_chart = alt.Chart(df[dist_chart_cols]).mark_line(opacity=0.6).encode(
            alt.X('date'),
            alt.Y('mean(distance):Q', scale=alt.Scale(domain=[0.8, 1.6])),
            alt.Color('CaBi Bike Type',
                    legend=alt.Legend(title=None, orient='top-left'),
                    scale=alt.Scale(range=['red', 'black']))
            )
    
    dist_chart.save('cabi_distance.html')

    # Average MPH by day
    mph_chart_cols = ['mph', 'date', 'CaBi Bike Type']
    mph_chart = alt.Chart(df[mph_chart_cols]).mark_line(opacity=0.6).encode(
            alt.X('date'),
            alt.Y('mean(mph):Q', scale=alt.Scale(domain=[5, 7])),
            alt.Color('CaBi Bike Type',
                    legend=alt.Legend(title=None, orient='top-left'),
                    scale=alt.Scale(range=['red', 'black']))
            )
    
    mph_chart.save('cabi_mph.html')
