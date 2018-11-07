import sys
sys.path.append("..")
import pandas as pd
import util_functions as uf
import altair as alt
from datetime import date

alt.renderers.enable('notebook')
alt.themes.enable('opaque')


def query(con):
    # Query Dockless Start by ANC and Overlaps
    return pd.read_sql("""WITH 		    
                            cabi_bikes AS (
                                SELECT DISTINCT 
                                bike_number,
                                MIN(start_date::timestamp::date) AS bike_min_date,
                                (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS bike_max_date
                                FROM cabi_trips
                                GROUP BY 1),
                            trips AS (select
                                start_date::date as date,
                                SUM(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') THEN 1 ELSE 0 END) as cabi_plus_trips,
                                SUM(CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') THEN 1 ELSE 0 END) as cabi_classic_trips,
                                COUNT(*) as Total_Trips,
                                (SUM(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z')THEN 1 ELSE 0 END) / COUNT(*) :: float) as CaBi_Plus_Trip_Perc
                                FROM cabi_trips 
                                WHERE start_date::date >= '2018-09-05'
                                GROUP BY 1)  

                            SELECT 
                            d.date::date,
                            /* CaBi Plus Trip Perc*/
                            cabi_plus_trips as "Cabi Plus Trips",
                            cabi_classic_trips as "Cabi Classic Trips",
                            Total_Trips as "Total Trips",
                            CaBi_Plus_Trip_Perc as "% of Trips",
                            /* CaBi Plus Fleet Perc*/
                            COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                            THEN cabi_bikes.bike_number ELSE NULL END) as cabi_plus_fleet,
                            COUNT(DISTINCT cabi_bikes.bike_number) as Total_Fleet,
                            (COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) not in ('?', 'w', 'W', 'Z') 
                            THEN cabi_bikes.bike_number ELSE NULL END) / COUNT(DISTINCT cabi_bikes.bike_number) :: float) as "% of Fleet"
                            FROM  generate_series(
                            '2018-09-05',
                            '2018-9-30',
                            interval '1 day') as d
                            /* CaBi Fleet*/
                            LEFT JOIN cabi_bikes as cabi_bikes
                            ON d.date::date BETWEEN cabi_bikes.bike_min_date AND cabi_bikes.bike_max_date
                            /* CABi Trips */
                            LEFT JOIN trips as trips
                            ON d.date::date = trips.date
                            GROUP BY 1, 2, 3, 4, 5;
                                            """, con=con)

if __name__ == "__main__":

    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = query(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
     # Melt dataframe for altair plot
    melted_df =  pd.melt(df, id_vars=['date'],
                            value_vars=['% of Trips', 
                                        '% of Fleet'],
                            var_name = 'CaBi Plus Stat Type'
                            )
    melted_df=melted_df.rename(columns = {'value':'CaBi Plus Stats'})
   
    # Merge on melted total trips
    melted_trips_df = pd.melt(df, id_vars=['date'],
                            value_vars=['Cabi Plus Trips', 
                                        'Cabi Classic Trips'],
                            var_name = 'CaBi Trip Type'
                            )
    melted_trips_df=melted_trips_df.rename(columns = {'value':'Total Daily Trips'})
    melted_df = pd.concat([melted_df, melted_trips_df[['CaBi Trip Type', 'Total Daily Trips']]], axis=1)
   
    # Chart    
    upper = alt.Chart(melted_df).mark_bar(opacity=0.8).encode(
                alt.X('date', title=" "),
                alt.Y('Total Daily Trips', title=" "),
                alt.Color('CaBi Trip Type',
                legend=alt.Legend(title=None, orient='top-left'),
                scale=alt.Scale(range=['red', 'black'])
                )
    ).properties(height=300)


    lower = alt.Chart(melted_df).mark_line(opacity=0.8).encode(
                alt.X('date', title=" "),
                alt.Y('CaBi Plus Stats', axis=alt.Axis(format='%'), title=" "),
                alt.Color('CaBi Plus Stat Type',
                legend=alt.Legend(title=None, orient='top-right'))
                ).properties(height=100)

    chart = alt.vconcat(upper, lower).resolve_scale(color='independent')

    chart.save('cabi_trips_fleet_perc.html')
