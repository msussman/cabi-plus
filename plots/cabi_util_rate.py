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


def cabi_util_rate(con):
    # Query Dockless Start by ANC and Overlaps
    return pd.read_sql("""WITH 		    
                            cabi_bikes AS (SELECT DISTINCT bike_number,
                                    MIN(start_date::timestamp::date) AS bike_min_date,
                                    (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS bike_max_date
                                    FROM cabi_trips
                                    GROUP BY 1),
                                    
                            cabi_trips AS (select 
                                    start_date::date as date,
                                    /* Traditional CaBi Count*/
                                    COUNT(CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as cabi_trips,
                                    /* CaBi Plus Count*/
                                    COUNT(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as cabi_plus_trips
                                    FROM cabi_trips
                                    WHERE start_date >= '2018-09-05'
                                    GROUP BY 1),
                                    
                            rain     AS (SELECT weather_date, 
                                                precipprobability
                                        FROM dark_sky_raw)

                            SELECT 
                            d.date::date,
                            rain.precipprobability as "Probability of Rain (%)",
                            cabi_trips.cabi_trips,
                            cabi_trips.cabi_plus_trips,
                            /* Traditional CaBi Count*/
                            COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) in ('?', 'w', 'W', 'Z') 
                            THEN cabi_bikes.bike_number ELSE NULL END) as cabi_bikes,
                            /* CaBi Plus Count*/
                            COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                            THEN cabi_bikes.bike_number ELSE NULL END) as cabi_plus_bikes
                            FROM generate_series(
                                        '2018-09-05',
                                        '2018-9-30',
                                        interval '1 day') as d    
                            /* Total CaBi Fleet Count*/
                            LEFT JOIN cabi_bikes as cabi_bikes
                            ON d.date::date BETWEEN cabi_bikes.bike_min_date AND cabi_bikes.bike_max_date
                            /* Total Trip Count*/
                            LEFT JOIN cabi_trips as cabi_trips
                            ON d.date::date = cabi_trips.date 
                            /* Daily Preciptation*/
                            LEFT JOIN rain as rain
                            on d.date::date = rain.weather_date
                            group by 1, 2, 3, 4;
                                            """, con=con)

if __name__ == "__main__":

    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = cabi_util_rate(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    # Calculate Utility rate
    df['CaBi Classic'] = df['cabi_trips'] / df['cabi_bikes']
    df['CaBi Plus'] =  df['cabi_plus_trips'] / df['cabi_plus_bikes']
    # Melt dataframe for altair plot
    melted_df =  pd.melt(df, id_vars=['date'],
                            value_vars=['CaBi Classic', 'CaBi Plus'],
                            var_name = 'CaBi Bike Type'
                            )
    melted_df=melted_df.rename(columns = {'value':'Daily Trips per Bike'})

    # Merge Probablility of Rain onto melted_Df
    weather_df = df[['date', 'Probability of Rain (%)']]
    melted_df = melted_df.merge(weather_df, on='date', how='left')
    # Utilization Rate Chart    
    base = alt.Chart(melted_df).encode(
    alt.X('date',
        #axis=alt.Axis(format='%b'),
        scale=alt.Scale(zero=False)
        )
    )

    bar = base.mark_bar(opacity=0.2).encode(
        alt.Y('Probability of Rain (%)'),
    )

    line =  base.mark_line(opacity=0.8).encode(
        alt.Y('Daily Trips per Bike'),
        alt.Color('CaBi Bike Type',
        legend=alt.Legend(title=None, orient='top-left'),
        scale=alt.Scale(range=['red', 'black']))
    )
    
    util_chart = alt.layer(line, bar).resolve_scale(y='independent')
    util_chart.save('cabi_util_rate.html')

    # CaBi Plus Trips % Above CaBi
    df['CaBi Plus Trips Per Bike, % Above CaBi'] = (df['CaBi Plus'] - df['CaBi Classic'])/ df['CaBi Classic']
    df.to_csv('cabi_util_rate.csv')

    util_perc_chart = alt.Chart(df).mark_line(opacity=0.6).encode(
                alt.X('date'),
                alt.Y('CaBi Plus Trips Per Bike, % Above CaBi', axis=alt.Axis(format='%'))
                )
    util_perc_chart.save('cabi_util_perc.html')
     

