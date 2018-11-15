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
                                    THEN bike_number ELSE NULL END) as cabi_plus_trips,
                                    /* Traditional CaBi Count*/
                                    COUNT(DISTINCT CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as cabi_classic_bikes_used,
                                    /* CaBi Plus Count*/
                                    COUNT(DISTINCT CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                                    THEN bike_number ELSE NULL END) as cabi_plus_bikes_used

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
                            cabi_trips.cabi_classic_bikes_used as cabi_classic_bikes,
                            cabi_trips.cabi_plus_bikes_used as cabi_plus_bikes,
                            /* CaBi Classic Fleet Count*/
                            COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) in ('?', 'w', 'W', 'Z') 
                            THEN cabi_bikes.bike_number ELSE NULL END) as cabi_classic_fleet,
                            /* CaBi Plus Fleet Count*/
                            COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                            THEN cabi_bikes.bike_number ELSE NULL END) as cabi_plus_fleet  
                            FROM generate_series(
                                        '2018-09-05',
                                        '2018-10-31',
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
                            group by 1, 2, 3, 4, 5, 6;
                                            """, con=con)

if __name__ == "__main__":

    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = cabi_util_rate(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    ''' Fleet '''

    # Calculate Utility rate
    df['CaBi Classic'] = df['cabi_trips'] / df['cabi_classic_fleet']
    df['CaBi Plus'] =  df['cabi_plus_trips'] / df['cabi_plus_fleet']
    print("CaBi Classic Avg Trips per Bike (Fleet):")
    print(df['cabi_trips'].sum() / df['cabi_classic_fleet'].sum())
    print("CaBi Plus Avg Trips per Bike (Fleet):")
    print(df['cabi_plus_trips'].sum() / df['cabi_plus_fleet'].sum())
    
    # Melt dataframe for altair plot
    fleet_df =  pd.melt(df, id_vars=['date'],
                            value_vars=['CaBi Classic', 
                                        'CaBi Plus',
                                        ],
                            var_name = 'CaBi Bike Type'
                            )
    fleet_df = fleet_df.rename(columns = {'value':'Daily Trips per Bike'})

    
    # Merge Probablility of Rain onto melted_Df
    weather_df = df[['date', 'Probability of Rain (%)']]
    fleet_df = fleet_df.merge(weather_df, on='date', how='left')

    '''Bikes Used'''

    df['CaBi Classic'] = df['cabi_trips'] / df['cabi_classic_bikes']
    df['CaBi Plus'] =  df['cabi_plus_trips'] / df['cabi_plus_bikes']
    print("CaBi Classic Avg Trips per Bike (Bikes Used):")
    print(df['cabi_trips'].sum() / df['cabi_classic_bikes'].sum())
    print("CaBi Plus Avg Trips per Bike (Bikes Used):")
    print(df['cabi_plus_trips'].sum() / df['cabi_plus_bikes'].sum())
    
    used_df =  pd.melt(df, id_vars=['date'],
                            value_vars=[
                                        'CaBi Classic',
                                        'CaBi Plus'],
                            var_name = 'CaBi Bike Type'
                            )
    used_df = used_df.rename(columns = {'value':'Daily Trips per Bike'})
    # Merge Probablility of Rain onto melted_Df
    weather_df = df[['date', 'Probability of Rain (%)']]
    used_df = used_df.merge(weather_df, on='date', how='left')
    
    # Fleet Chart    
    base = alt.Chart(fleet_df, title= 'Trips per Bike (Total Fleet)').encode(
    alt.X('date', title=" ",
        #axis=alt.Axis(format='%b'),
        scale=alt.Scale(zero=False)
        )
    )

    bar = base.mark_bar(opacity=0.2).encode(
        alt.Y('Probability of Rain (%)'),
    )

    line =  base.mark_line(opacity=0.8).encode(
        alt.Y('Daily Trips per Bike', scale=alt.Scale(domain=[0, 12])),
        alt.Color('CaBi Bike Type',
        legend=alt.Legend(title=None, orient='top-left'),
        scale=alt.Scale(range=['red', 'black']))
    )

    fleet_chart = alt.layer(line, bar).resolve_scale(y='independent')

    #Bikes Used Chart
    base = alt.Chart(used_df, title= 'Trips per Bike (Bikes Used)').encode(
    alt.X('date', title=" ",
        #axis=alt.Axis(format='%b'),
        scale=alt.Scale(zero=False)
        )
    )

    bar = base.mark_bar(opacity=0.2).encode(
        alt.Y('Probability of Rain (%)'),
    )

    line =  base.mark_line(opacity=0.8).encode(
        alt.Y('Daily Trips per Bike', scale=alt.Scale(domain=[0, 12])),
        alt.Color('CaBi Bike Type',
        legend=alt.Legend(title=None, orient='top-left'),
        scale=alt.Scale(range=['red', 'black']))
    )

    used_chart = alt.layer(line, bar).resolve_scale(y='independent')

    # Comvbine charts and save

    util_chart = fleet_chart | used_chart

    util_chart.save('../plots_output/cabi_util_rate.html')
     

