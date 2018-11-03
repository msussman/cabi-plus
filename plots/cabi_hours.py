import pandas as pd
import sys
import seaborn as sns
sys.path.append("..")
import util_functions as uf
import matplotlib.pyplot as plt
import numpy as np



def query(con):
    # queries bikeshare db
    return pd.read_sql("""WITH 
                          join_op_status AS (
                          SELECT 
                          trips.*, 
                          op_status,
                          day_of_week,
                          CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
                          THEN 'CaBi Classic' 
                          ELSE 'CaBi Plus' END as cabi_bike_type
                          FROM cabi_trips as trips
                          LEFT JOIN metro_hours AS hours
                          ON extract('DOW' FROM trips.start_date) = hours.day_of_week 
                          AND trips.start_date::time BETWEEN hours.start_time AND hours.end_time
                          WHERE start_date::date >= '2018-09-05'
                          AND member_type  = 'Member'),

                          bike_type_totals AS (
                          SELECT
                          cabi_bike_type,
                          COUNT(*) as cabi_bike_type_total
                          FROM join_op_status
                          GROUP by 1
                          ) 

                        SELECT DISTINCT
                        status.cabi_bike_type AS "CaBi Trip Type",
                        day_of_week as "Day of Week",
                        op_status as "Metro Operating Hours Status",
                        cabi_bike_type_total,
                        COUNT(*) AS cabi_trips
                        FROM join_op_status as status
                        LEFT JOIN bike_type_totals as totals
                        ON status.cabi_bike_type = totals.cabi_bike_type 
                        GROUP BY 1, 2, 3, 4
                        ORDER BY 1, 2, 3, 4;
                        """, con=con)

if __name__ == "__main__":
    conn, cur = uf.local_connect()
    # Return Dataframe of Percent of Trips by ANC
    df = query(con=conn)
    df['Percent of Total Weekly Trips'] = df['cabi_trips'] / df['cabi_bike_type_total']
    # Change Value of Sunday to 7 instead of 0
    df['Day of Week'] = np.where(df['Day of Week'] == 0, 7, df['Day of Week'])
    # Make Value of Metro Operating Hours Status properized
    proper_dict = {'no_service':'No Metro Service',
                   'regular': 'Regular Operating Hours',
                   'peak': 'Peak Operating Hours'}
    df["Metro Operating Hours Status"] = df["Metro Operating Hours Status"].map(proper_dict) 
    # Generate side by side bar plots
    g = sns.factorplot(
        x='Day of Week', y='Percent of Total Weekly Trips',
        hue='Metro Operating Hours Status', col='CaBi Trip Type', data=df, kind='bar',
        palette='muted', col_order=['CaBi Classic', 'CaBi Plus'],
        legend=False, size=4, aspect=1)
    g.set_xticklabels(
            ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun'],
            fontsize=8)
    g.set_xlabels('', fontsize=10)
    g.set_ylabels('Percent of Total Trips', fontsize=10)
    plt.legend(bbox_to_anchor=(0.9, -0.2), borderaxespad=0., ncol=3, title='Metro Operating Hours')
    g.savefig("../plots_output/cabi_hours.png")


