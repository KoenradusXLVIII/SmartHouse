<?php
// Show errors
ini_set('display_errors', 1);

// Headers
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');  

// Includes
include_once '../config/new_database.php';

// Connect to database
$database = new Database();
$db = $database->getConnection();

// Query database
$leftAxis = $_GET["leftAxis"];
$rightAxis = $_GET["rightAxis"];
$query = sprintf("SELECT meas.sensor_id, meas.timestamp, meas.value, sensors.name AS sensor_name, quantities.name AS quantity_name, quantities.uom FROM meas LEFT JOIN sensors ON meas.sensor_id = sensors.id LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE meas.sensor_id IN (" . $leftAxis . "," . $rightAxis . ") AND DATE(timestamp)=CURDATE() ORDER BY timestamp ASC");
$result = $db->query($query);

// Loop through the returned data
$data = array();
foreach ($result as $row) {
	$data[] = $row;
}

// Free memory associated with result
$result->free();

// Close connection
$db->close();

//now print the data
print json_encode($data);

?>