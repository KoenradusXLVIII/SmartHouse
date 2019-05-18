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
                    <h2>All SensorNodes</h2>
                    [<a href="intraday.php">Intraday</a>] [<a href="nodes.php">Nodes</a>] [<a href="sensor_table.php">Sensors</a>] [<a href="trail_table.php">Trail</a>]<br /><br />
                    <div class="table-responsive">
                        <table id="nodes" class="table table-striped table-bordered">
                          <thead>
                            <tr>
                              <th>User</th>
                              <th>Name</th>
                              <th>UUID</th>
                              <th>Status</th>
                              <th>Last seen</th>
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
                                $query = "SELECT * FROM nodes ORDER BY name ASC";
                                $result = $db->query($query);
                                
                                // Loop through the returned data
                                if($result) {
                                    foreach ($result as $node) {
                                        // Query database
                                        $query = "SELECT users.name AS user, nodes.id, nodes.name, meas.timestamp FROM nodes LEFT JOIN users ON users.id = nodes.user_id LEFT JOIN sensors ON sensors.node_id = nodes.id LEFT JOIN meas ON meas.sensor_id = sensors.id WHERE node_id = '" . $node['id'] ."' ORDER BY timestamp DESC LIMIT 1";
                                        $result = $db->query($query);
                                        $row = $result->fetch_assoc();
                                        
                                        echo "<tr>";
                                        echo "<td>" . ucfirst($row['user'])  . "</td>";
                                        echo "<td>" . $row['name']  . "</td>";
                                        echo "<td>" . $row['id']  . "</td>";
                                        if (strtotime($row['timestamp']) <= strtotime('-10 minutes')) {
                                            echo "<td><span class=\"badge badge-danger\">offline</span></td>";
                                        } else {
                                            echo "<td><span class=\"badge badge-success\">online</span></td>";
                                        }
                                        echo "<td>" . $row['timestamp']  . "</td>";
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
                <div class="col-md-3"></div>
            </div>
        </div>
            
        <script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
        <script src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/1.10.19/js/dataTables.bootstrap4.min.js"></script>
		<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>
        <script type="text/javascript">
            $(document).ready(function(){
                $('#nodes').DataTable();
            } );
        </script>
    </body>
</html>
