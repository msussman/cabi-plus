/* by Date*/

SELECT
start_date::date as date,
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
AVG(end_date - start_date) as avg_trip_dur
FROM cabi_trips
WHERE start_date::date >= '2018-09-05'
      AND end_date > start_date
GROUP BY 1, 2;


/*by DOW 0 = Sunday*/

SELECT
extract(dow from start_date) as dow,
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
AVG(end_date - start_date) as avg_trip_dur
FROM cabi_trips
WHERE start_date::date >= '2018-09-05'
      AND end_date > start_date
GROUP BY 1, 2;

/* by date, members only*/
SELECT
start_date::date as date,
CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
     THEN 'CaBi' 
     ELSE 'CaBi Plus' END as bike_type,
AVG(end_date - start_date) as avg_trip_dur
FROM cabi_trips
WHERE start_date::date >= '2018-09-05'
      AND end_date > start_date
      AND member_type = 'Member'
GROUP BY 1, 2;