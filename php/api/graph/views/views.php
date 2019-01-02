<?php
    // Show errors
    ini_set('display_errors', 1);
    
    // Headers
    header('Content-Type: application/json');
    header('Access-Control-Allow-Origin: *');  
    
    // Includes
    include_once '../../config/database.php';
    
    // Connect to database
    $database = new Database();
    $db = $database->getConnection();
    
    if($_POST["method"]=="GET_NAME") {
        // Query database
        $query = "SELECT id FROM views WHERE name='" . $_POST["view_name"] . "' AND user_id='" . $_POST["user_id"] . "'";
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
    } elseif($_POST["method"]=="GET_VIEW") {
        $data = array();
        $data['left_axis'] = array();
        $data['right_axis'] = array();
        
        // Query the database for the left axis sensors
        $query = "SELECT sensor_id FROM views_sensors LEFT JOIN views ON views_sensors.view_id = views.id WHERE views_sensors.axis = 0 AND views_sensors.view_id=" . $_POST["view_id"] . " AND views.user_id='" . $_POST["user_id"] . "'";
        $result = $db->query($query);
        
        // Loop through the returned data
        if($result) {
            foreach ($result as $row) {
        	    array_push($data['left_axis'],$row['sensor_id']);
            }
            
            // Free memory associated with result
            $result->free();
        } 
        
        // Query the database for the left axis sensors
        $query = "SELECT sensor_id FROM views_sensors LEFT JOIN views ON views_sensors.view_id = views.id WHERE views_sensors.axis = 1 AND views_sensors.view_id=" . $_POST["view_id"] . " AND views.user_id='" . $_POST["user_id"] . "'";
        $result = $db->query($query);
        
        // Loop through the returned data
        if($result) {
            foreach ($result as $row) {
        	    array_push($data['right_axis'],$row['sensor_id']);
            }
            
            // Free memory associated with result
            $result->free();
        }         
    } elseif($_POST["method"]=="ALL") {
        // Query database
        $query = "SELECT id, name FROM views WHERE user_id='" . $_POST["user_id"] . "'";
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
    } elseif($_POST["method"]=="DEL") {
        // Query database
        $query = "DELETE views_sensors FROM views_sensors LEFT JOIN views ON views_sensors.view_id = views.id WHERE view_id=" . $_POST["view_id"] . " AND views.user_id='" . $_POST["user_id"] . "'";
        $result = $db->query($query);
        
        // Query database
        $query = "DELETE views FROM views WHERE id=" . $_POST["view_id"] . " AND user_id='" . $_POST["user_id"] . "'";
        $result = $db->query($query);
    } elseif($_POST["method"]=="POST") {
        // Store view
        $query = "INSERT INTO views (`name`,`user_id`) VALUES ('" . $_POST["view_name"] . "', '" . $_POST["user_id"] . "')";
        $result = $db->query($query);
        
        // Retrieve view ID
        $query = "SELECT id FROM views WHERE name ='" . $_POST["view_name"] . "' AND user_id='" . $_POST["user_id"] . "'";
        $result = $db->query($query);
        $row = $result->fetch_assoc();
        
        // Store left axis sensors in view
        if($_POST["left_axis"]) {
            foreach($_POST["left_axis"] as $sensor) {
                $query = "INSERT INTO views_sensors (`view_id`,`sensor_id`,`axis`) VALUES ('" . $row['id'] . "', '" . $sensor . "', 0)";
                $result = $db->query($query);
            }
        }
        
        // Store left axis sensors in view
        if($_POST["right_axis"]) {
            foreach($_POST["right_axis"] as $sensor) {
                $query = "INSERT INTO views_sensors (`view_id`,`sensor_id`,`axis`) VALUES ('" . $row['id'] . "', '" . $sensor . "', 1)";
                $result = $db->query($query);
            }        
        }
    }
    
    // Close connection
    $db->close();
    
    //now print the data
    print json_encode($data);

?>