<?php
// Show errors
ini_set('display_errors', 1);

// Headers
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');  

// Includes
include_once '../config/database.php';

// Connect to database
$database = new Database();
$db = $database->getConnection();

// Query database
$query = "SELECT meas.sensor_id, meas.timestamp, meas.value, sensors.name AS sensor_name, quantities.name AS quantity_name, quantities.uom FROM meas ";
$query = $query . "LEFT JOIN sensors ON meas.sensor_id = sensors.id LEFT JOIN quantities ON sensors.quantity_id = quantities.id ";
$query = $query . "WHERE DATE(timestamp) = '" . $_POST["graph_date"] . "' AND meas.sensor_id IN (";
foreach ($_POST["sensors"] as $sensor) {
    $query = $query . $sensor . ",";
}
$query = rtrim($query, ',') . ") AND timestamp >= NOW() - INTERVAL 2 DAY ORDER BY timestamp ASC";
$result = $db->query($query);

// Loop through the returned data
$data = array();
if($result) {
    foreach ($result as $row) {
	    $data[] = $row;
    }
    
    // Free memory associated with result
    $result->free();
}

// Close connection
$db->close();

//now print the data
print json_encode($data);

?>