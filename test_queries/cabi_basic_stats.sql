SELECT
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
COUNT(*) as trips,
COUNT(distinct bike_number) as bikes,
AVG(end_date - start_date) as avg_trip_dur,
SUM(CASE WHEN member_type = 'Member' THEN 1 ELSE 0 END)/COUNT(*)::float as perc_members 

FROM cabi_trips
WHERE start_date >= '2018-09-05'
GROUP BY 1;