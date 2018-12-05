SELECT
EXTRACT('MONTH' from start_date::date) as month,
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
COUNT(*) as trips,
COUNT(distinct bike_number) as bikes,
AVG(end_date - start_date) as avg_trip_dur,
SUM(CASE WHEN member_type = 'Member' THEN 1 ELSE 0 END)/COUNT(*)::float as perc_members,
SUM(CASE WHEN member_type = 'Casual' THEN 1 ELSE 0 END) as casual_trips,
SUM(CASE WHEN member_type = 'Member' THEN 1 ELSE 0 END) as member_trips
FROM cabi_trips
WHERE start_date >= '2018-09-05'
AND start_date < '2018-12-01'
GROUP BY 1, 2
ORDER By 2, 1;