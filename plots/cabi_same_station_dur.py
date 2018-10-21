import sys
sys.path.append("..")
import pandas as pd
import numpy as np
import util_functions as uf
import altair as alt
import json
import requests
from datetime import date

alt.renderers.enable('notebook')
alt.themes.enable('opaque')


def query(con):
    # queries bikeshare db
    return pd.read_sql("""SELECT
                        CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                            THEN 'CaBi' 
                            ELSE 'CaBi Plus' END as "CaBi Bike Type",
                        end_date - start_date as "Trip Duration",
                        count(*) as "Total Trips"
                        FROM cabi_trips
                        WHERE start_date::date >= '2018-09-05'
                            AND end_date > start_date
                            AND start_station = end_station
                            AND member_type = 'Member'
                            AND (end_date - start_date) < '01:00:00'
                        group by 1, 2
                        order by 1, 2;
                        """, con=con)

if __name__ == "__main__":

    # Generating Data
    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = query(con=conn)
    # Convert timedelta to float of minutes
    df['Trip Duration (minutes)'] = df['Trip Duration'] / np.timedelta64(1, 'm')
    # Calculate cumulative percentage by
    df['cumsum'] = df.groupby(["CaBi Bike Type"])['Total Trips'].transform('cumsum')
    df['Cumulative Percent of Total Trips'] = df.groupby(["CaBi Bike Type"])['cumsum'].transform(lambda x: x / x.iloc[-1])
    
    chart_cols = ['Trip Duration (minutes)', 'Cumulative Percent of Total Trips', 'CaBi Bike Type']
    chart = alt.Chart(df[chart_cols]).mark_line(opacity=0.6).encode(
            alt.X('Trip Duration (minutes)'),
            alt.Y('Cumulative Percent of Total Trips', axis=alt.Axis(format='%')),
            alt.Color('CaBi Bike Type',
                    legend=alt.Legend(title=None, orient='top-left'),
                    scale=alt.Scale(range=['red', 'black']))
            )
    
    chart.save('cabi_same_station_dur.html')
