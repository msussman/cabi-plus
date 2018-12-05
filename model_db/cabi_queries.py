import pandas as pd


def cabi_trips_by_member(conn):
    # CaBi Trips by Member Type and Region (joined on)
    df = pd.read_sql("""SELECT DISTINCT
                        start_date::date as date,
                        member_type,
                        /*Total Trips*/
                        COUNT(*) as cabi_trips
                        from cabi_trips as trips
                        WHERE start_date::date < '2018-12-01'
                        GROUP by 1, 2;
                 """, con=conn)
    return df


def cabi_bikes_available(conn):
    # Calculate Cabi Bike Available based on bike min and max usage date, will ultimately be replaced by true CaBi Bike History
    df = pd.read_sql("""SELECT ds.weather_date as date,
                          COUNT(DISTINCT cabi_bikes.bike_number) as cabi_bikes_avail
                          FROM dark_sky_raw as ds
                          LEFT JOIN
                            (SELECT DISTINCT bike_number,
                            MIN(start_date::timestamp::date) AS bike_min_date,
                              (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS bike_max_date

                            FROM cabi_trips
                            WHERE start_date::date < '2018-12-01'
                            GROUP BY 1) as cabi_bikes
                          ON ds.weather_date BETWEEN cabi_bikes.bike_min_date AND cabi_bikes.bike_max_date
                          GROUP BY 1;
                     """, con=conn)
    return df


def cabi_stations_available(conn):
    # Calculate Cabi stations Available based on station min and max usage date, will ultimately be replaced by true CaBi Station History
    df = pd.read_sql("""SELECT ds.weather_date as date,
                        COUNT(DISTINCT cabi_stations.station) as cabi_stations,
                        SUM(cabi_stations.docks) as cabi_docks
                        FROM dark_sky_raw as ds
                        LEFT JOIN
                        ((select distinct
                          station,
                          MIN(station_min_date) AS station_min_date,
                          MAX(station_max_date) AS station_max_date,
                          SUM(capacity) as docks
                          from
                          /* Stack start and end station history from cabi trips*/
                          (((SELECT DISTINCT
                            start_station as station,
                            MIN(start_date::timestamp::date) AS station_min_date,
                            (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS station_max_date
                            FROM cabi_trips
                            WHERE start_date::date < '2018-12-01'
                            GROUP BY 1)
                          union
                          (SELECT DISTINCT
                            end_station as station,
                            MIN(start_date::timestamp::date) AS station_min_date,
                            (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS station_max_date
                            FROM cabi_trips
                            WHERE start_date::date < '2018-12-01'
                            GROUP BY 1)) as stations
                          /* Bring on Region Code from cabi station and system API data*/
                          JOIN (SELECT distinct
                                     short_name,
                                     capacity
                                     FROM cabi_stations
                                     LEFT JOIN cabi_system
                                     ON cabi_stations.region_id = cabi_system.region_id) as region_code
                                     ON stations.station = region_code.short_name
                                     )
                          GROUP BY 1
                          ORDER BY 1)) as cabi_stations
                        ON ds.weather_date BETWEEN cabi_stations.station_min_date AND cabi_stations.station_max_date              
                        GROUP BY 1;
                        """, con=conn)
    return df

