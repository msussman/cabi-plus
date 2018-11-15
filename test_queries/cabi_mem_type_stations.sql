WITH 
cabi_casual AS (SELECT *
		FROM cabi_trips
		WHERE member_type = 'Casual'
		AND start_date::date >= '2018-09-05'
		AND end_date > start_date)
,
cabi_member AS (SELECT *
		FROM cabi_trips
		WHERE member_type = 'Member'
		AND start_date::date >= '2018-09-05'
		AND end_date > start_date)

/* CaBi Casual Trips by Station*/
SELECT DISTINCT
'Casual' as member_type, 
start_station,
stations.name AS start_name,
count(*) AS total_trips
FROM cabi_casual as trips
LEFT JOIN cabi_stations as stations
ON trips.start_station = stations.short_name
GROUP by 1, 2, 3
ORDER by 4 DESC;

/* CaBi Member Trips by Station*/
SELECT DISTINCT
'Member' as member_type, 
start_station,
stations.name AS start_name,
count(*) AS total_trips
FROM cabi_member as trips
LEFT JOIN cabi_stations as stations
ON trips.start_station = stations.short_name
GROUP by 1, 2, 3
ORDER by 4 DESC;