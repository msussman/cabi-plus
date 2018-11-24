import sqlite3
import pandas as pd
from datetime import date

# Establish Connection
con = sqlite3.connect(r'data/for_ml.db')
cur = con.cursor() 

df = pd.read_sql("""SELECT 
                    *
                    FROM final_db;
                    """, con=con)
# Convert date to datetime column
df['date'] = pd.to_datetime(df['date'])
print(df.head())
print(df.columns)
print(df.dtypes)

