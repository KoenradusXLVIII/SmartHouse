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
        <style type="text/css">
            .multiselect-container > li > a > label.checkbox
            {
                width: 350px;
            }
            .btn-group > .btn:first-child
            {
                width: 350px;
            }
        </style>
	</head>
	<body>
        <div class="container-narrow">
            <div>
                <h3 class="muted">SensorNode [last 48h]</h3>
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
                    //$query = sprintf("SELECT sensors.id, sensors.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id WHERE user_id = 1 ORDER BY name ASC");
                    $query = "SELECT DISTINCT quantities.id,  quantities.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id";
                    $result = $db->query($query);
                    
                    // Populate dropdown
                    echo "<select id='LeftAxisDropdown' onchange='updateLeftMultiDrop()' style='border-width:0px'>";
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
                <select id="LeftAxisMultiDropdown" multiple="multiple" onchange='updateGraph()'></select>
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
                    $query = "SELECT DISTINCT quantities.id, quantities.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id";
                    $result = $db->query($query);
                    
                    // Populate dropdown
                    echo "<select id='RightAxisDropdown' onchange='updateRightMultiDrop()' style='border-width:0px'>";
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
                <select id="RightAxisMultiDropdown" multiple="multiple" onchange='updateGraph()'>
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
            function updateLeftMultiDrop() {
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/sensors.php",
                    dataType:'json',
                    method: "POST",
                    data: {quantity_id: $('#LeftAxisDropdown').val()},
                    success: function(data) {
                        $('#LeftAxisMultiDropdown').empty();
                        for (var i in data) {
                            var option = document.createElement("option");
                            option.text = data[i].name;
                            option.value = data[i].id;
                            $('#LeftAxisMultiDropdown').append(option);
                            $('#LeftAxisMultiDropdown').multiselect('rebuild');
                        }
                    },
                    error: function(response){
                        console.log(response);
                    }
                });
            }
            
            function updateRightMultiDrop() {
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/sensors.php",
                    dataType:'json',
                    method: "POST",
                    data: {quantity_id: $('#RightAxisDropdown').val()},
                    success: function(data) {
                        $('#RightAxisMultiDropdown').empty();
                        for (var i in data) {
                            var option = document.createElement("option");
                            option.text = data[i].name;
                            option.value = data[i].id;
                            $('#RightAxisMultiDropdown').append(option);
                            $('#RightAxisMultiDropdown').multiselect('rebuild');
                        }
                    },
                    error: function(response){
                        console.log(response);
                    }
                });
            }
        
            function updateGraph() {
              var left_axis = $('#LeftAxisMultiDropdown').val();
              var right_axis = $('#RightAxisMultiDropdown').val();
              $('#graph-canvas').remove(); // this is my <canvas> element
              $('#graph-container').append('<canvas id="graph-canvas"><canvas>');
              renderChart(left_axis,right_axis);
            }
        </script>
	</body>
</html>