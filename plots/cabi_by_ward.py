import sys
sys.path.append("..")
import pandas as pd
import numpy as np
import util_functions as uf
import json
import requests
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Point
from datetime import date
import seaborn as sns


def extract_json(json_id):
    # Loop through each feature in GeoJson and pull our metadata and polygon
    url = "https://opendata.arcgis.com/datasets/{}.geojson".format(json_id)
    resp = requests.get(url).json()
    # Define empty list for concat
    feature_df_list = []
    for enum, feature in enumerate(resp['features']):
        # Pull out metadata
        feature_df = pd.DataFrame(feature['properties'], index=[enum])
        # Convert Polygon geometry to geodataframe
        geometry_df = gpd.GeoDataFrame(feature['geometry'])
        # Convert geometry to polygon and add back to metadata dataframe
        feature_df['polygon'] = Polygon(geometry_df['coordinates'].iloc[0])
        feature_df_list.append(feature_df)
    # Combine each Cluster into master dataframe
    combined_df = pd.concat(feature_df_list, axis=0)
    # convert combined_df to geodataframe
    combined_df = gpd.GeoDataFrame(combined_df, geometry='polygon')
    return combined_df


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
                            end_coords.lon as end_lon                            
                            FROM cabi_trips as cabi_trips
                            /* JOIN on start station lat, lon */
                            LEFT JOIN station_coords as start_coords
                            ON cabi_trips.start_station = start_coords.short_name
                            /* JOIN on end station lat, lon */
                            LEFT JOIN station_coords as end_coords
                            ON cabi_trips.end_station = end_coords.short_name

                            WHERE start_date::date >= '2018-09-05'
                            AND start_date < '2018-12-01'
                            AND end_date > start_date
                            AND member_type = 'Member'
                            ;
                        """, con=con)


if __name__ == "__main__":
    # Import Ward geojson as dataframe
    json_id_dict = {'ward': "0ef47379cbae44e88267c01eaec2ff6e_31"}
    ward_df = extract_json(json_id_dict['ward'])
    # Connect local database
    conn, cur = uf.local_connect()
    # Return Dataframe all CaBi Trips marked as CaBi Plus or Not and lat lon
    df = query(con=conn)
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    # convert dataframe to geodataframe
    df['Coordinates'] = list(zip(df['start_lon'], df['start_lat']))
    df['Coordinates'] = df['Coordinates'].apply(Point)
    gdf = gpd.GeoDataFrame(df, geometry='Coordinates')
    # Merge on ward to points dataframe
    gdf = gpd.sjoin(gdf, ward_df[['WARD', 'polygon']], op='within') 
    # Count of trips by Ward (index) by CaBi Trip Type(columns) 
    table = pd.pivot_table(gdf[['WARD', 'CaBi Bike Type']], 
                          index=['WARD'],
                          columns=['CaBi Bike Type'], 
                          aggfunc=len)
    
    print(table)
    table.to_csv('../plots_output/month3/by_ward.csv')
