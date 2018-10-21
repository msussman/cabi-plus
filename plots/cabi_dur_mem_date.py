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
                        start_date::date as date,
                        CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                            THEN 'CaBi' 
                            ELSE 'CaBi Plus' END as "CaBi Bike Type",
                        AVG(end_date - start_date) as "Average Trip Duration for Members"
                        FROM cabi_trips
                        WHERE start_date::date >= '2018-09-05'
                            AND end_date > start_date
                            AND member_type = 'Member'
                        GROUP BY 1, 2;
                        """, con=con)

if __name__ == "__main__":
    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = query(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    # Convert timedelta to float of minutes
    df['Average Trip Duration for Members'] = df['Average Trip Duration for Members'] / np.timedelta64(1, 'm')
    
    print(df.groupby('CaBi Bike Type')['Average Trip Duration for Members'].mean())

    # Utilizatiom  Rate Chart
    chart = alt.Chart(df).mark_line(opacity=0.6).encode(
                alt.X('date'),
                alt.Y('Average Trip Duration for Members', scale=alt.Scale(domain=[10, 25])),
                alt.Color('CaBi Bike Type',
                        legend=alt.Legend(title=None, orient='top-left'),
                        scale=alt.Scale(range=['red', 'black']))
                )
    chart.save('cabi_dur_mem_date.html')
     

