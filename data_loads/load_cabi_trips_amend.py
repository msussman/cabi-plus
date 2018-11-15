import pandas as pd 
import os 
import sys
sys.path.append("..")
import util_functions as uf
 
# Define function to pull CaBi Trip data from DDOT source 
 
 
if __name__ == "__main__": 
    # Connect to local bikeshare DB
    conn, cur = uf.local_connect() 
    # Convert May - September 2018 trip data from CSV to dataframe
    csv_list = [f for f in sorted(os.listdir('../cabi_data')) if f.endswith(".csv")]

    df_list = []    
    for csv in csv_list:
        csv_path = os.path.join('../cabi_data', csv)
        df = pd.read_csv(csv_path).drop(['Start station', 'End station'], axis=1)
        df.columns = ['duration', 'start_date', 'end_date', 'start_station', 'end_station', 'bike_number', 'member_type'] 
        df_list.append(df)

    combined_df = pd.concat(df_list, axis=0)
    # Add trip_id continuing from last record in AWS table 
    trip_id_df = pd.read_sql("""SELECT trip_id from cabi_trips order by trip_id desc LIMIT 1 """, con=conn) 
    last_trip_id = trip_id_df['trip_id'].iloc[0] 
    combined_df.reset_index(inplace=True) 
    combined_df['trip_id'] = combined_df.index + 1 + last_trip_id 
    # Drop unneeded fields 
    combined_df.drop(['index'], axis=1, inplace=True) 
    # Output dataframe as CSV 
    # Define start and end months based on file names 
    outname = "CaBi_Trip_Data_2018010" 
    combined_df.to_csv(outname + ".csv", index=False, sep='|') 
 
    # Load to Database 
    uf.local_load(outname, "cabi_trips", cur) 
 
    # Commit changes to database 
    conn.commit() 