/* Members*/

SELECT
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
SUM(CASE WHEN start_station = end_station THEN 1 ELSE 0 END)/COUNT(*)::float as perc_same_start_stop 
FROM cabi_trips
WHERE start_date::date >= '2018-09-05'
      AND end_date > start_date
      AND member_type = 'Member'
GROUP BY 1;

/* Duration of trips less than an hour*/

SELECT
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
MIN(end_date - start_date) as min_trip_dur,  
AVG(end_date - start_date) as avg_trip_dur,
MAX(end_date - start_date) as max_trip_dur  
FROM cabi_trips
WHERE start_date::date >= '2018-09-05'
      AND end_date > start_date
      AND start_station = end_station
      AND member_type = 'Member'
      AND (end_date - start_date) < '01:00:00'
GROUP BY 1;

/*Distribution of Same Station Trips */

SELECT
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
end_date - start_date as trip_dur,
count(*) as trips
FROM cabi_trips
WHERE start_date::date >= '2018-09-05'
      AND end_date > start_date
      AND start_station = end_station
      AND member_type = 'Member'
      AND (end_date - start_date) < '01:00:00'
group by 1, 2
order by 1, 2;