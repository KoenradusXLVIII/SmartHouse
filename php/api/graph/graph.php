<?php
   include('session.php');
?>

<!DOCTYPE html>
<html>
	<head>
		<title>SensorNode</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-multiselect/0.9.15/css/bootstrap-multiselect.css" integrity="sha256-7stu7f6AB+1rx5IqD8I+XuIcK4gSnpeGeSjqsODU+Rk=" crossorigin="anonymous" />
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
                <p>&copy; Joost Verberk 2018 <a href="logout.php">[Log out]</a></p>
            </div>
        </div> <!-- /container -->

		<!-- javascript -->
		<script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.23.0/moment.js" integrity="sha256-l6SU+rVSlkyIcMsqjy0mb6ne/qPpYotdVSFd9vLmV1A=" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js" integrity="sha384-wHAiFfRlMFy6i5SRaxvfOCifBUQy1xHdJ/yoi7FRNXMRBu5WHdZYu1hA6ZOblgut" crossorigin="anonymous"></script>
		<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-multiselect/0.9.15/js/bootstrap-multiselect.min.js"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.3/Chart.min.js" integrity="sha256-oSgtFCCmHWRPQ/JmR4OoZ3Xke1Pw4v50uh6pLcu+fIc=" crossorigin="anonymous"></script>
		<script type="text/javascript" src="js/app.js"></script>

        <script type="text/javascript">
            $(document).ready(function(){
            	$('#LeftAxisMultiDropdown').multiselect('rebuild');
            	$('#RightAxisMultiDropdown').multiselect('rebuild');
            	renderChart([3],[5,6]);
            });
        
            function updateLeftMultiDrop() {
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/sensors.php",
                    dataType:'json',
                    method: "POST",
                    data: {quantity_id: $('#LeftAxisDropdown').val(), user_id: <?php echo $_SESSION['user_id'];?>},
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
                    data: {quantity_id: $('#RightAxisDropdown').val(), user_id: <?php echo $_SESSION['user_id'];?>},
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