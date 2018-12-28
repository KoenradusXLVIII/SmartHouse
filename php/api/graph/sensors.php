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
$query = "SELECT id, name FROM sensors WHERE quantity_id = " . $_POST["quantity_id"];
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