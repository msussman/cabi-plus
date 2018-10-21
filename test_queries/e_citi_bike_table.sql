CREATE TABLE e_citi_bikes as select bike_number 
from (select distinct
bike_number,
min(start_date::date) as bike_start_date
from citi_trips
group by 1) as bike_starts
where '2018-08-20' <= bike_Start_date and bike_Start_date <= '2018-08-25';