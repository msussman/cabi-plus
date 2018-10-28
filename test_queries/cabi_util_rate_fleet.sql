WITH 		    
cabi_bikes AS (SELECT DISTINCT bike_number,
    MIN(start_date::timestamp::date) AS bike_min_date,
    (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS bike_max_date
    FROM cabi_trips
    GROUP BY 1),

cabi_bike_count as (SELECT start_date::date as date,
/* CaBi Classic Count*/
COUNT(CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
THEN bike_number ELSE NULL END) as cabi_trips,
/* CaBi Plus Count*/
COUNT(CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
THEN bike_number ELSE NULL END) as cabi_plus_trips,
/* CaBi Classic Bikes w/ at least one trip */
COUNT(DISTINCT CASE WHEN left(bike_number, 1) in ('?', 'w', 'W', 'Z') 
THEN bike_number ELSE NULL END) as cabi_bikes,
/* CaBi Plus Bikes w/ at least one trip */
COUNT(DISTINCT CASE WHEN left(bike_number, 1) not in ('?', 'w', 'W', 'Z') 
THEN bike_number ELSE NULL END) as cabi_plus_bikes
FROM cabi_trips
WHERE start_date >= '2018-09-05'
GROUP BY 1
)

SELECT cabi_bike_count.*,
COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) not in ('?', 'w', 'W', 'Z') 
THEN cabi_bikes.bike_number ELSE NULL END) as cabi_plus_fleet,
COUNT(DISTINCT CASE WHEN left(cabi_bikes.bike_number, 1) in ('?', 'w', 'W', 'Z') 
THEN cabi_bikes.bike_number ELSE NULL END) as cabi_fleet
FROM cabi_bike_count as cabi_bike_count
LEFT JOIN cabi_bikes as cabi_bikes
ON cabi_bike_count.date BETWEEN cabi_bikes.bike_min_date AND cabi_bikes.bike_max_date
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1