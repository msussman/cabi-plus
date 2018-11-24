import pandas as pd
import cabi_queries as cabi
import secondary_queries as second
from psycopg2 import sql
import time
from functools import reduce
import holidays
import numpy as np
import sqlite3
import sys
sys.path.append("..")
import util_functions as uf


def cabi_agg_results(group_by_cols, drop_cols):
    # Aggregate the results from the CaBi Trip SQl query to different levels
    df = cabi_trips_df.drop(drop_cols, axis=1).groupby(group_by_cols).sum()
    return df


def cabi_cal_avgs(df):
    # For SQL efficiency, calculate averages from Cabi Trip data total fields
    calc_columns = [col for col in df.columns if "_tot" in col]
    for calc_column in calc_columns:
        avg_column = calc_column.replace('_tot', '_avg')
        df[avg_column] = df[calc_column] / df['cabi_trips']
    return df


def df_unstack(in_df, level):
    # Unstack Cabi Trips query results to make wide by descriptive field (ie Region and Member Type)
    df = in_df.unstack(level=level)
    df = pd.DataFrame(df.to_records()).set_index('date')
    df.columns = [hdr.replace("('", "").replace("', '", "_").replace("')", "") for hdr in df.columns]
    return df


def cabi_sum(sum_type, df):
    # Aggegrate sum type across regions
    sum_cols = [col for col in df if sum_type in col]
    series = df[sum_cols].sum(axis=1)
    return series


def date_to_datetime_type(df):
    # Convert date from dataframe to datetime types and set as index
    df['date'] = df['date'].astype('datetime64[ns]')
    df.set_index(['date'], inplace=True)
    return df


if __name__ == "__main__":
    # Connect to local db
    conn, cur = uf.local_connect()

    # Gather all Secondary Data sources
    print("Gather Secondary Data Sources")

    # Dark Sky Weather Data
    dark_sky_df = second.dark_sky(conn)
    dark_sky_df = date_to_datetime_type(dark_sky_df)
    # Federal Holidays Observed
    us_holidays = holidays.UnitedStates()
    us_holidays_df = pd.DataFrame(dark_sky_df.index, columns = ['date'])
    us_holidays_df['us_holiday'] = us_holidays_df['date'].apply(lambda x: x in us_holidays).astype(int)
    us_holidays_df.set_index(['date'], inplace=True)

    # Washington Nationals Home Game Data
    nats_df = second.nats_games(conn)
    nats_df = date_to_datetime_type(nats_df)

    # DC Population, merge by year and month
    dcpop_df = second.dc_pop(conn)

    # Merge all secondary Data together
    second_dfs = [dark_sky_df, us_holidays_df, nats_df]
    second_df = reduce(lambda left, right: pd.merge(left, right, how='left', left_index=True, right_index=True), second_dfs)
    second_df.drop_duplicates(inplace=True)
    second_df.reset_index(inplace=True)
    # Merge on DC popualation data by year and month
    second_df = second_df.merge(dcpop_df, how='left', on=['year', 'month'])
    second_df.set_index('date', inplace=True)
    # Dockless Pilot 1/0 between September 9th, 2017 and end of 2018
    second_df['dobi_pilot'] = np.where(second_df.index >= '2017-09-07', 1, 0) 
    # Export to CSV
    second_df.to_csv("second.csv", index=True, sep='|')
    
    print("Start CaBi Processing")
    # CABI: Generate Dataframe of Cabi Trip Stats by Region and Member
    cabi_trips_df = cabi.cabi_trips_by_member(conn)
    cabi_trips_df['date'] = cabi_trips_df['date'].astype('datetime64[ns]')    
    # Unstack by Member
    cabi_trips_df.set_index(['date', 'member_type'], inplace=True)
    cabi_trips_df_unstack = df_unstack(in_df=cabi_trips_df, level=[-1])
    # Calculate total CaBi Trips priper day
    cabi_trips_df_unstack['cabi_trips'] = cabi_trips_df_unstack.sum(axis=1) 
    # CABI: CaBi Bike Available
    cabi_bikes_df = cabi.cabi_bikes_available(conn)
    cabi_bikes_df['date'] = cabi_bikes_df['date'].astype('datetime64[ns]')
    cabi_bikes_df.set_index('date', inplace=True)
    # CABI: CaBi Stations Available
    cabi_stations_df = cabi.cabi_stations_available(conn)
    cabi_stations_df.set_index('date', inplace=True)
    
    # Merge all CaBI DFs together
    cabi_dfs = [cabi_trips_df_unstack,                
                cabi_bikes_df,
                cabi_stations_df]

    cabi_df = reduce(lambda left, right: pd.merge(left, right, how='left', left_index=True, right_index=True), cabi_dfs)    
    cabi_df.fillna(0, inplace=True)
    # Calculate CaBi Syste Utilization Rate
    cabi_df['cabi_util_rate'] = cabi_df['cabi_trips'] / cabi_df['cabi_bikes_avail']
    cabi_df.to_csv("cabi.csv", index=True, sep='|')
    # Merge all DFs together
    final_dfs = [second_df, cabi_df]
    df_final = reduce(lambda left, right: pd.merge(left, right, how="left", left_index=True, right_index=True), final_dfs)
    df_final.drop_duplicates(inplace=True)
    
    # Fill all na with 0 and reset index 
    df_final.fillna(0, inplace=True)
    df_final.reset_index(inplace=True)

    # Output final DataFrame
    outname = "final_db_pipe_delimited"
    df_final.to_csv(outname + ".csv", index=False, sep='|')

    # CREATE TABLE on sqlite db with and without timestamp
    lite_conn = sqlite3.connect(r"../ml/data/for_ml.db")

    # Load df_final to final_db table of sqllite db
    df_final.to_sql('final_db',
                     con=lite_conn,
                     if_exists='replace',
                     index=False)
