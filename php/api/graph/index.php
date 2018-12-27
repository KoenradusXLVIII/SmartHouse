<!DOCTYPE html>
<html>
	<head>
		<title>SensorNode</title>
        <link href="css/bootstrap.min.css" rel="stylesheet" type="text/css" />
        <link href="css/bootstrap-multiselect.css" rel="stylesheet" type="text/css" />
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
	</head>
	<body>
        <div class="container-narrow">
            <div>
                <h3 class="muted">SensorNode</h3>
                <b>Left axis</b><br />
                
                <?php
                    // Show errors
                    ini_set('display_errors', 1);
    
                    // Includes
                    include_once '../config/database.php';
                    
                    // Connect to database
                    $database = new Database();
                    $db = $database->getConnection();
                    
                    // Query database
                    $query = sprintf("SELECT * FROM quantities");
                    $result = $db->query($query);
                    
                    // Query database
                    $query = sprintf("SELECT sensors.id, sensors.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE user_id = 1 ORDER BY name ASC");
                    $result = $db->query($query);
                    
                    // Populate dropdown
                    echo "<select id='LeftAxisDropdown' onchange='updateGraph()' style='border-width:0px'>";
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
                ?>
                <select id="left_sensors" multiple="multiple"></select>
                </select>
                <br />
                
                <b>Right axis</b><br />
                <?php
                    // Show errors
                    ini_set('display_errors', 1);
    
                    // Includes
                    include_once '../config/database.php';
                    
                    // Connect to database
                    $database = new Database();
                    $db = $database->getConnection();
                    
                    // Query database
                    $query = sprintf("SELECT sensors.id, sensors.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE user_id = 1 ORDER BY name ASC");
                    $result = $db->query($query);
                    
                    // Populate dropdown
                    echo "<select id='RightAxisDropdown' onchange='updateGraph()' style='border-width:0px'>";
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
                ?>                
                <select id="right_sensors" multiple="multiple">
                </select>
                <br /><br />                
                
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
		<script type="text/javascript" src="js/jquery.min.js"></script>
		<script type="text/javascript" src="js/moment.min.js"></script>
		<script type="text/javascript" src="js/bootstrap.bundle.min.js"></script>
		<script type="text/javascript" src="js/bootstrap-multiselect.js"></script>
		<script type="text/javascript" src="js/chart.min.js"></script>
		<script type="text/javascript" src="js/app.js"></script>

        <script type="text/javascript">
            function updateGraph() {
              var left_axis = document.getElementById("LeftAxisDropdown").value;
              var right_axis = document.getElementById("RightAxisDropdown").value;
              $('#graph-canvas').remove(); // this is my <canvas> element
              $('#graph-container').append('<canvas id="graph-canvas"><canvas>');
              renderChart(left_axis,right_axis);
            }
        </script>
	</body>
</html>