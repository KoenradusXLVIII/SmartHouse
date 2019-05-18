<?php
   include('session.php');
?>

<!DOCTYPE html>
<html>
	<head>
		<title>SensorNode</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"  integrity="sha384-wvfXpqpZZVQGK6TAh5PVlGOfQNHSoD2xbE+QkPxCAFlNEevoEH3Sl0sibVcOQVnN" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdn.datatables.net/1.10.19/css/dataTables.bootstrap4.min.css">
        <style type="text/css">
          body {
            padding-top: 20px;
            padding-bottom: 40px;
          }
        </style>
	</head>
	<body>
	    <div class="container">
            <div class="row">
        	    <div class="col-md-10">
                    <h2>Sensors</h2>
                    [<a href="intraday.php">Intraday</a>] [<a href="nodes.php">Nodes</a>] [<a href="sensor_table.php">Sensors</a>] [<a href="trail_table.php">Trail</a>]<br /><br />
                    <div class="table-responsive">
                        <table id="sensors" class="table table-striped table-bordered">
                          <thead>
                            <tr>
                              <th>Node</th>
                              <th>Name</th>
                              <th>Quantity</th>
                              <th>Last value</th>
                              <th>Last update</th>
                            </tr>
                          </thead>
                          <tbody>
                              <?php
                                // Includes
                                include_once '../config/database.php';
                                
                                // Connect to database
                                $database = new Database();
                                $db = $database->getConnection();
                                
                                // Query database
                                $query = "SELECT sensors.id FROM sensors LEFT JOIN nodes ON sensors.node_id = nodes.id WHERE user_id = '" . $_SESSION['user_id'] . "' ORDER BY sensors.name ASC";
                                $result = $db->query($query);
                                
                                // Loop through the returned data
                                if($result) {
                                    foreach ($result as $row) {
        	                            // Query database
                                        $query = "SELECT nodes.name AS node, sensors.name AS sensor, quantities.name AS quantity, quantities.uom, meas.timestamp, meas.value FROM nodes LEFT JOIN sensors ON sensors.node_id = nodes.id LEFT JOIN meas ON meas.sensor_id = sensors.id LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE sensors.id = '" . $row['id'] . "' AND user_id = '" . $_SESSION['user_id'] ."' ORDER BY timestamp DESC LIMIT 1";
                                        $result = $db->query($query);
                                        $line = $result->fetch_assoc();
                                        
                                        echo "<tr>";
                                        echo "<td>" . $line['node']  . "</td>";
                                        echo "<td>" . $line['sensor']  . "</td>";
                                        echo "<td>" . $line['quantity'] . "</td>";
                                        echo "<td>" . $line['value']  . " " . $line['uom'] . "</td>";
                                        echo "<td>" . $line['timestamp']  . "</td>";
                                        echo "</tr>";
                                    }
                                }
                              ?>
                          </tbody>
                        </table>
                    </div>
                    <div class="footer">
                        <p>&copy; SensorNode - Joost Verberk - 2018 <a href="logout.php">[Log out]</a></p>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
        <script src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/1.10.19/js/dataTables.bootstrap4.min.js"></script>
		<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>
        <script type="text/javascript">
            $(document).ready(function(){
                $('#sensors').DataTable();
            } );
        </script>
        
    </body>
</html>
