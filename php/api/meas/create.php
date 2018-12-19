<?php
// Rate limitation
session_start();
if (isset($_SESSION['LAST_CALL'])) {
  $last = strtotime($_SESSION['LAST_CALL']);
  $curr = strtotime(date("Y-m-d h:i:s"));
  $sec =  abs($last - $curr);
  if ($sec <= 60) {
    $data = 'Rate Limit Exceeded';  // rate limit
    header('Content-Type: application/json');
    die (json_encode($data));
  }
}
$_SESSION['LAST_CALL'] = date("Y-m-d h:i:s");

// required headers
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Max-Age: 3600");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

// includes
include_once '../config/database.php';
include_once '../objects/meas.php';

$database = new Database();
$db = $database->getConnection();

$meas = new Meas($db);

// get posted data
$data = json_decode(file_get_contents("php://input"));

// make sure data is not empty
if (!empty($data->sensor_id) && !empty($data->value)){
    // set product property values
    $meas->sensor_id = $data->sensor_id;
    $meas->value = $data->value;

    // create the product
    if($meas->create()){

        // set response code - 201 created
        http_response_code(201);

        // tell the user
        echo json_encode(array("message" => "Measurement was stored."));
    }

    // if unable to create the product, tell the user
    else{

        // set response code - 503 service unavailable
        http_response_code(503);

        // tell the user
        echo json_encode(array("message" => "Unable to store the measurement."));
    }
}

// tell the user data is incomplete
else{

    // set response code - 400 bad request
    http_response_code(400);

    // tell the user
    echo json_encode(array("message" => "Unable to store the measurement. Data is incomplete."));
}
?>