select 
 d.date::date,
 citi_trips.citi_trips,
 citi_trips.citi_plus_trips,
 /* Traditional Citi Count*/
  COUNT(DISTINCT CASE WHEN citi_bikes.e_bike = 0 
	THEN citi_bikes.bike_number ELSE NULL END) as citi_bikes,
 /* Electric Citi Count*/
 COUNT(DISTINCT CASE WHEN citi_bikes.e_bike = 1 
       THEN citi_bikes.bike_number ELSE NULL END) as citi_plus_bikes
 FROM
 generate_series(
           '2018-08-20',
           '2018-9-30',
           interval '1 day') as d  
/*Bikes During Time Period */
LEFT JOIN
(SELECT DISTINCT 
trips.bike_number,
/* flag ebikes*/
CASE WHEN e_bikes.bike_number is not null 
	THEN 1 ELSE 0 END as e_bike,
MIN(start_date::date) AS bike_min_date,
(date_trunc('month', MAX(start_date)) + interval '1 month')::date AS bike_max_date
FROM citi_trips as trips
LEFT JOIN e_citi_bikes as e_bikes
on trips.bike_number = e_bikes.bike_number
GROUP BY 1, 2) as citi_bikes
ON d.date::date BETWEEN citi_bikes.bike_min_date AND citi_bikes.bike_max_date
/* Total Trip Count*/
LEFT JOIN
(select 
start_date::date as date,
 /* Traditional Citi Count*/
 COUNT(CASE WHEN e_bikes.bike_number is null 
	THEN trips.bike_number ELSE NULL END) as citi_trips,
 /* Citi Plus Count*/
 COUNT(CASE WHEN e_bikes.bike_number is not null
       THEN trips.bike_number ELSE NULL END) as citi_plus_trips
FROM citi_trips as trips
LEFT JOIN e_citi_bikes as e_bikes
on trips.bike_number = e_bikes.bike_number
WHERE start_date >= '2018-08-20'
GROUP BY 1) as citi_trips
ON d.date::date = citi_trips.date 
group by 1, 2, 3;
