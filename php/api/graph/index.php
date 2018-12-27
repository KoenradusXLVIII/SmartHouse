<!DOCTYPE html>
<html>
	<head>
		<title>SensorNode</title>
        <link href="css/bootstrap-2.3.2.min.css" rel="stylesheet">
        <style type="text/css">
          body {
            padding-top: 20px;
            padding-bottom: 40px;
          }
    
          /* Custom container */
          .container-narrow {
            margin: 0 auto;
            max-width: 700px;
          }
          .container-narrow > hr {
            margin: 30px 0;
          }
    
          /* Main marketing message and sign up button */
          .jumbotron {
            margin: 60px 0;
            text-align: left;
          }
          .jumbotron h1 {
            font-size: 72px;
            line-height: 1;
          }
          .jumbotron h2 {
            font-size: 36px;
            line-height: 1;
            text-align: center;
          }
          .jumbotron .btn {
            font-size: 21px;
            padding: 14px 24px;
          }
    
          /* Supporting marketing content */
          .marketing {
            margin: 60px 0;
          }
          .marketing p + h4 {
            margin-top: 28px;
          }
        </style>
        <link href="css/bootstrap-responsive-2.3.2.min.css" rel="stylesheet">
	</head>
	<body>
        <div class="container-narrow">
            <div class="masthead">
                <ul class="nav nav-pills pull-right">
                    <li class="active"><a href="#">Home</a></li>
                    <li><a href="#">About</a></li>
                    <li><a href="#">Contact</a></li>
                </ul>
                <h3 class="muted">SensorNode</h3>
            </div>
            
            <hr>
            
            <div class="jumbotron">
                <b>Left axis</b><br />
                <?php
                    // Show errors
                    ini_set('display_errors', 1);
    
                    // Includes
                    include_once '../config/new_database.php';
                    
                    // Connect to database
                    $database = new Database();
                    $db = $database->getConnection();
                    
                    // Query database
                    $query = sprintf("SELECT sensors.id, sensors.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE user_id = 1 ORDER BY name ASC");
                    $result = $db->query($query);
                    
                    // Populate dropdown
                    echo "<select id='LeftAxisDropdown' onchange='updateGraph()'>";
                    while ($row = $result->fetch_assoc()) {
                        if ($row['id']==3)
                        {
                            echo "<option value='" . $row['id'] . "' selected='selected'>" . $row['name'] . " [" . $row['uom'] . "]</option>";
                        } else {
                            echo "<option value='" . $row['id'] . "'>" . $row['name'] . " [" . $row['uom'] . "]</option>";
                        }
                    }
                    echo "</select>";
                    
                    // Free memory associated with result
                    $result->free();
                    
                    // Close connection
                    $db->close();
                ?><br />
                <b>Right axis</b><br />
                <?php
                    // Show errors
                    ini_set('display_errors', 1);
    
                    // Includes
                    include_once '../config/new_database.php';
                    
                    // Connect to database
                    $database = new Database();
                    $db = $database->getConnection();
                    
                    // Query database
                    $query = sprintf("SELECT sensors.id, sensors.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE user_id = 1 ORDER BY name ASC");
                    $result = $db->query($query);
                    
                    // Populate dropdown
                    echo "<select id='RightAxisDropdown' onchange='updateGraph()'>";
                    while ($row = $result->fetch_assoc()) {
                        if ($row['id']==4)
                        {
                            echo "<option value='" . $row['id'] . "' selected='selected'>" . $row['name'] . " [" . $row['uom'] . "]</option>";
                        } else {
                            echo "<option value='" . $row['id'] . "'>" . $row['name'] . " [" . $row['uom'] . "]</option>";
                        }
                    }
                    echo "</select>";
                    
                    // Free memory associated with result
                    $result->free();
                    
                    // Close connection
                    $db->close();
                ?><br /><br />                
                <div id="graph-container">
                    <canvas id="graph-canvas" width="700"></canvas>
                </div>
            </div>
    
            <hr>
    
            <div class="footer">
                <p>&copy; Joost Verberk 2018</p>
            </div>
        </div> <!-- /container -->

		<!-- javascript -->
		<script type="text/javascript" src="js/jquery-3.3.1.min.js"></script>
		<script type="text/javascript" src="js/moment-2.23.0.min.js"></script>
		<script type="text/javascript" src="js/bootstrap-2.3.2.min.js"></script>
		<script type="text/javascript" src="js/chart-2.7.3.min.js"></script>
		<script type="text/javascript" src="js/app.js"></script>

        <script type="text/javascript">
            function updateGraph() {
              var left = document.getElementById("LeftAxisDropdown").value;
              var right = document.getElementById("RightAxisDropdown").value;
              $('#graph-canvas').remove(); // this is my <canvas> element
              $('#graph-container').append('<canvas id="graph-canvas"><canvas>');
              renderChart(left,right);
            }
        </script>
	</body>
</html>