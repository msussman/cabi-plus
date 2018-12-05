import sys
sys.path.append("..")
import pandas as pd
import util_functions as uf
import altair as alt
import json
import requests
from datetime import date

alt.renderers.enable('notebook')
alt.themes.enable('opaque')


def query(con):
    return pd.read_sql("""WITH 		    	      
                            daily_trips AS (select 
                                    start_date::date as date,
                                    /* Traditional CaBi Count*/
                                    COUNT(CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as daily_cabi_trips,
                                    /* CaBi Plus Count*/
                                    COUNT(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as daily_cabi_plus_trips,
                                    /* CaBi Plus Bikes Count*/
                                    COUNT(DISTINCT CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as "CaBi Plus Bikes w/ Trips"
                                    FROM cabi_trips
                                    WHERE start_date >= '2018-09-05'
                                    GROUP BY 1),
                            total_trips AS (select 
                                    /* Traditional CaBi Count*/
                                    COUNT(CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as total_cabi_trips,
                                    /* CaBi Plus Count*/
                                    COUNT(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as total_cabi_plus_trips
                                    FROM cabi_trips
                                    WHERE start_date >= '2018-09-05'
                                    AND start_date < '2018-12-01'
                                    )

                            SELECT 
                            daily_trips.*,
                            total_trips.*,
                            daily_cabi_trips/total_cabi_trips::float as "CaBi Classic",
                            daily_cabi_plus_trips/total_cabi_plus_trips::float as "CaBi Plus"
                            FROM daily_trips as daily_trips
                            LEFT JOIN total_trips as total_trips
                            ON daily_trips.date = daily_trips.date
                            ORDER by date

                                            """, con=con)

if __name__ == "__main__":

    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = query(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Melt dataframe for altair plot
    melted_df =  pd.melt(df, id_vars=['date'],
                            value_vars=['CaBi Classic', 'CaBi Plus'],
                            var_name = 'CaBi Bike Type'
                            )
    melted_df=melted_df.rename(columns = {'value':'Daily Percent of Total Trips'})

    # Merge CaBi Plus Bikes 
    cabi_df = df[['date', 'CaBi Plus Bikes w/ Trips']]
    melted_df = melted_df.merge(cabi_df, on='date', how='left')

    base = alt.Chart(melted_df).encode(
    alt.X('date',
        #axis=alt.Axis(format='%b'),
        scale=alt.Scale(zero=False)
        )
    )

    bar = base.mark_bar(opacity=0.2, color='black').encode(
        alt.Y('CaBi Plus Bikes w/ Trips'),
    )

    line =  base.mark_line(opacity=0.8).encode(
        alt.Y('Daily Percent of Total Trips'),
        alt.Color('CaBi Bike Type',
        legend=alt.Legend(title=None, orient='bottom-left'),
        scale=alt.Scale(range=['red', 'black']))
    )
    
    chart = alt.layer(line, bar).resolve_scale(y='independent')
    chart.save('../plots_output/month3/cabi_daily_perc.html')
     

