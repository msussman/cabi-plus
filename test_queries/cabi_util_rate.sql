select 
 d.date::date,
 cabi_trips.cabi_trips,
 cabi_trips.cabi_plus_trips,
 /* Traditional CaBi Count*/
  COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) in ('?', 'w', 'W', 'Z') 
	THEN cabi_bikes.bike_number ELSE NULL END) as cabi_bikes,
 
 /* CaBi Plus Count*/
 COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) not in ('?', 'w', 'W', 'Z') 
       THEN cabi_bikes.bike_number ELSE NULL END) as cabi_plus_bikes
 FROM
 generate_series(
           '2018-09-01',
           '2018-9-30',
           interval '1 day') as d  
/*Traditional CaBi */
LEFT JOIN
(SELECT DISTINCT bike_number,
MIN(start_date::timestamp::date) AS bike_min_date,
(date_trunc('week', MAX(start_date)) + interval '1 week')::date AS bike_max_date
FROM cabi_trips
GROUP BY 1) as cabi_bikes
ON d.date::date BETWEEN cabi_bikes.bike_min_date AND cabi_bikes.bike_max_date
/* Total Trip Count*/
LEFT JOIN
(select 
start_date::date as date,
 /* Traditional CaBi Count*/
 COUNT(CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
	THEN bike_number ELSE NULL END) as cabi_trips,
 /* CaBi Plus Count*/
 COUNT(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
       THEN bike_number ELSE NULL END) as cabi_plus_trips
FROM cabi_trips
WHERE start_date >= '2018-09-01'
GROUP BY 1) as cabi_trips
ON d.date::date = cabi_trips.date 
group by 1, 2, 3;