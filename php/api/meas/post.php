<?php
// Show errors
ini_set('display_errors', 1);

// Includes
include_once '../config/database.php';

// Parameters
$interval = 5;

// Connect to database
$database = new Database();
$db = $database->getConnection();

// Get posted data
$data = json_decode(file_get_contents("php://input"));

// Verify API key and retrieve user ID
$query = "SELECT id FROM users WHERE api_key = '" . $data->api_key . "'";
$result = $db->query($query);
$row = $result->fetch_assoc();

if (!empty($row)) {
    // User authorized to upload data
    $user_id = $row['id'];
    // Upload each measurement in the payload
    $list = $data->values;
    foreach($list as $item) {
        $query = "SELECT sensors.name FROM sensors LEFT JOIN nodes ON sensors.node_id = nodes.id WHERE sensors.id = " . $item->sensor_id . " AND nodes.user_id='" . $user_id . "'";    
        echo $query;
        $result = $db->query($query);
        $row = $result->fetch_assoc();
        if(!empty($row)) {
            // User is allowed to upload data to this sensor
            
            // Get the current 5-minute upload interval
            $start_date = new DateTime();
            $seconds = $start_date->format('s');
            $start_date->modify('-' . $seconds . ' seconds');
            $minute = $start_date->format('i');
            $start_date->modify('-' . ($minute % $interval) . ' minutes');
            $end_date = clone $start_date;
            $end_date->modify('+5 minutes');
            
            $query = "SELECT * FROM meas WHERE sensor_id = " . $item->sensor_id . " AND timestamp >= '" . $start_date->format('Y-m-d H:i:s') . "' AND timestamp < '" . $end_date->format('Y-m-d H:i:s') . "' LIMIT 1";
            $result = $db->query($query);
            $row = $result->fetch_assoc();
            if(empty($row)) {
                // First upload for this 5-minute time interval, write new value
                $query = "INSERT INTO meas (`timestamp`, `sensor_id`, `value`) VALUES ('" . $start_date->format('Y-m-d H:i:s') . "', '" . $item->sensor_id . "', '" . $item->value . "')";
                $result = $db->query($query);
            } else {
                // Not first upload for this 5-minute time interval, update previous value
                $query = "UPDATE meas SET `value` = '" . $item->value . "' WHERE `id` = '" . $row['id'] . "'";
                $result = $db->query($query);
            }
        }
    }
}
?>