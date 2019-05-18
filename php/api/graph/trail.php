<?php
// Show errors
ini_set('display_errors', 1);

// Includes
include_once '../config/database.php';

// Connect to database
$database = new Database();
$db = $database->getConnection();

// Get posted data
$data = json_decode(file_get_contents("php://input"));


// Verify API key and retrieve user ID
$query = "SELECT count(users.id) FROM users LEFT JOIN nodes ON nodes.user_id = users.id WHERE nodes.id = '" . $data->node_uuid . "' AND users.api_key = '" . $data->api_key . "'";
$result = $db->query($query);
$row = $result->fetch_assoc();

if (!empty($row)) {
    // User authorized to upload message to trail
    $query = "INSERT INTO trail (`node_id`,`level`,`event`) VALUES ('" . $data->node_uuid . "', '" .$data->level . "', '" . $data->message . "')";
    $result = $db->query($query);
    if($result) {
        echo "200 OK";
    } else {
        echo "500 Internal Server Error";
    }
} else {
    echo "401 Unauthorized";
}
?>