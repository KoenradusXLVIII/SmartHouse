<?php

// Includes
include_once '../config/database.php';
include_once '../objects/meas.php';

// Connect to database
$database = new Database();
$db = $database->getConnection();

// Get posted data
$data = json_decode(file_get_contents("php://input"));

// Verify API key and retrieve user ID
$query = "SELECT id FROM users WHERE api_key = '" . $data->api_key . "'";
$stmt = $db->prepare($query);
$stmt->execute();
$row = $stmt->fetch(PDO::FETCH_ASSOC);
if (!empty($row)) {
    // User authorized to upload data
    $user_id = $row['id'];
    // Upload each measurement in the payload
    $list = $data->values;
    foreach($list as $item) {
        $query = "SELECT name FROM sensors WHERE id = " . $item->sensor_id . " AND user_id=" . $user_id;    
        $stmt = $db->prepare($query);
        $stmt->execute();
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if(!empty($row)) {
            // User is allowed to upload data to this sensor
            $query = "INSERT INTO meas (`sensor_id`, `value`) VALUES ('" . $item->sensor_id . "', '" . $item->value . "')";
            $stmt = $db->prepare($query);
            $stmt->execute();
        }
    }
}
?>