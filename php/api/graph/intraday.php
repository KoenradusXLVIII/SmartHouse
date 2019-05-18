<?php
   include('session.php');
?>

<!DOCTYPE html>
<html>
	<head>
		<title>SensorNode</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-multiselect/0.9.15/css/bootstrap-multiselect.css" integrity="sha256-7stu7f6AB+1rx5IqD8I+XuIcK4gSnpeGeSjqsODU+Rk=" crossorigin="anonymous" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.8.0/css/bootstrap-datepicker.css" integrity="sha256-9w7XtQnqRDvThmsQHfLmXdDbGasYsSjF6FSXrDh7F6g=" crossorigin="anonymous" />
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"  integrity="sha384-wvfXpqpZZVQGK6TAh5PVlGOfQNHSoD2xbE+QkPxCAFlNEevoEH3Sl0sibVcOQVnN" crossorigin="anonymous">
        <link rel="icon" href="favicon.ico" type="image/x-icon" />
        <style type="text/css">
          body {
            padding-top: 20px;
            padding-bottom: 40px;
          }
        </style>
        <style type="text/css">
            .multiselect-container > li > a > label.checkbox
            {
                width: 350px;
                padding: 3px 20px 3px 10px;
            }
            .btn-group > .btn:first-child
            {
                width: 350px;
            }
        </style>
	</head>
	<body>
	    <div class="container">
            <div class="row">
        	    <div class="col-md-10">
                    <h2>Intraday</h2>
                    [<a href="intraday.php">Intraday</a>] [<a href="nodes.php">Nodes</a>] [<a href="sensor_table.php">Sensors</a>] [<a href="trail_table.php">Trail</a>]<br /><br />
                    <b>Personal views</b><br />
                    <select id='ViewDropdown' onchange='viewChange()' style='border-width:0px'>
                    </select>&nbsp;&nbsp;
                    <button onclick="viewDelete()">Delete</button>&nbsp;&nbsp;
                    <button onclick="viewFav()">Set as favourite</button>&nbsp;&nbsp;
                    <button onclick="viewStore()">Store</button>&nbsp;&nbsp;
                    <input type="text" id="viewName" placeholder="Unique view name">&nbsp;&nbsp;<span id="viewStoreStatus"></span>
                    <br /><br />
                    
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
                        $query = "SELECT DISTINCT quantities.id,  quantities.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id LEFT JOIN nodes ON sensors.node_id = nodes.id WHERE nodes.user_id = '" . $_SESSION['user_id'] ."'";
                        $result = $db->query($query);
                        
                        // Populate dropdown
                        echo "<select id='LeftAxisDropdown' onchange='updateLeftMultiDrop()' style='border-width:0px'>";
                        while ($row = $result->fetch_assoc()) {
                            echo "<option value='" . $row['id'] . "'>" . $row['name'] . " [" . $row['uom'] . "]</option>";
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
                        $query = "SELECT DISTINCT quantities.id,  quantities.name, quantities.uom FROM sensors LEFT JOIN quantities ON sensors.quantity_id = quantities.id LEFT JOIN nodes ON sensors.node_id = nodes.id WHERE nodes.user_id = '" . $_SESSION['user_id'] . "'";
                        $result = $db->query($query);
                        
                        // Populate dropdown
                        echo "<select id='RightAxisDropdown' onchange='updateRightMultiDrop()' style='border-width:0px'>";
                        while ($row = $result->fetch_assoc()) {
                            echo "<option value='" . $row['id'] . "'>" . $row['name'] . " [" . $row['uom'] . "]</option>";
                        }
                        echo "</select>";
                        
                        // Free memory associated with result
                        $result->free();
                        
                        // Close connection
                        $db->close();
                    ?>                
                    <select id="RightAxisMultiDropdown" multiple="multiple" onchange='updateGraph()'>
                    </select>
                    <br />  
                    <b>Date</b><br/>
    
                    <div class="form-group">
                        <div class='input-group date' id='datepicker1' data-target-input='nearest'>
                            <input id="datepicker" type='text' class="form-control datepicker-input" data-target="#datepicker1" value="<?php echo date("d-m-Y"); ?>">
                            <div class="input-group-append" data-target="#datepicker" data-toggle="datepicker">
                                <div class="input-group-text">
                                    <i class="fa fa-calendar"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <br />
                    
                    <div id="graph-container">
                        <canvas id="graph-canvas" width="400"></canvas>
                    </div> 
                    <br />
                    <div class="footer">
                        <p>&copy; SensorNode - Joost Verberk - 2018 <a href="logout.php">[Log out]</a></p>
                    </div>
                </div>
            </div>
        </div>
    
        

		<!-- javascript -->
		<script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.23.0/moment.js" integrity="sha256-l6SU+rVSlkyIcMsqjy0mb6ne/qPpYotdVSFd9vLmV1A=" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js" integrity="sha384-wHAiFfRlMFy6i5SRaxvfOCifBUQy1xHdJ/yoi7FRNXMRBu5WHdZYu1hA6ZOblgut" crossorigin="anonymous"></script>
		<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-multiselect/0.9.15/js/bootstrap-multiselect.min.js"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.8.0/js/bootstrap-datepicker.min.js" integrity="sha256-tW5LzEC7QjhG0CiAvxlseMTs2qJS7u3DRPauDjFJ3zo=" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.3/Chart.min.js" integrity="sha256-oSgtFCCmHWRPQ/JmR4OoZ3Xke1Pw4v50uh6pLcu+fIc=" crossorigin="anonymous"></script>
		<script type="text/javascript" src="js/app.js"></script>

        <script type="text/javascript">
            $(document).ready(function(){
                $('#datepicker').datepicker({
                    orientation: 'bottom',
                    format: 'dd-mm-yyyy'
                });
            	$('#LeftAxisMultiDropdown').multiselect('rebuild');
            	updateLeftMultiDrop();
            	$('#RightAxisMultiDropdown').multiselect('rebuild');
            	updateRightMultiDrop();
            	viewDropdownUpdate();
            	setTimeout(viewChange,1000);
            });
            
            $('#datepicker').on('changeDate', function() {
                viewChange();    
            });
            
            function viewDelete() {
                var view_id = $('#ViewDropdown').val();
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/views/views.php",
                    dataType:'json',
                    method: "POST",
                    data: {method: "DEL", view_id: view_id, user_id: '<?php echo $_SESSION['user_id'];?>'},
                    success: function(data) {
                        viewDropdownUpdate();  
                        setTimeout(viewChange,1000);
                    },
                    error: function(response){
                        console.log(response);
                    }
                });                
            }
            
            function viewDropdownUpdate() {
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/views/views.php",
                    dataType:'json',
                    method: "POST",
                    data: {method: "ALL", user_id: '<?php echo $_SESSION['user_id'];?>'},
                    success: function(data) {  
                        $('#ViewDropdown').empty();
                        for (var i in data) {
                            var option = document.createElement("option");
                            option.text = data[i].name;
                            option.value = data[i].id;
                            $('#ViewDropdown').append(option);
                        }    
                    },
                    error: function(response){
                        console.log(response);
                    }
                });
            }
            
            function viewChange() {
                var view_id = $('#ViewDropdown').val();
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/views/views.php",
                    dataType:'json',
                    method: "POST",
                    data: {method: "GET_VIEW", view_id: view_id, user_id: '<?php echo $_SESSION['user_id'];?>'},
                    success: function(data) {
                        $('#graph-canvas').remove(); // this is my <canvas> element
                        $('#graph-container').append('<canvas id="graph-canvas"><canvas>');
                        var graph_date = $('#datepicker').data('datepicker').getFormattedDate('yyyy-mm-dd');
                        renderChart(data.left_axis,data.right_axis,graph_date);    
                    },
                    error: function(response){
                        console.log(response);
                    }
                });    
            }
            
            function viewStore() {
                var view_name = $('#viewName').val();
                if (view_name) {
                    // viewName cannot be empty
                    // now check if viewName is unique
                    $.ajax({
                        url: "http://www.joostverberk.nl/api/graph/views/views.php",
                        dataType:'json',
                        method: "POST",
                        data: {method: "GET_NAME", view_name: view_name, user_id: '<?php echo $_SESSION['user_id'];?>'},
                        success: function(data) {
                            if(data.length==0) {
                                // viewName must be unique
                                var left_axis = $('#LeftAxisMultiDropdown').val();
                                var right_axis = $('#RightAxisMultiDropdown').val();
                                $.ajax({
                                    url: "http://www.joostverberk.nl/api/graph/views/views.php",
                                    dataType:'json',
                                    method: "POST",
                                    data: {method: "POST", view_name: view_name, left_axis: left_axis, right_axis: right_axis, user_id: '<?php echo $_SESSION['user_id'];?>'},
                                    success: function(data) {
                                        $('#viewStoreStatus').html('<span class="badge badge-success">OK</span>');
                                        viewDropdownUpdate();
                                    },
                                    error: function(response){
                                        console.log(response);
                                    }
                                });
                            } else {
                                $('#viewStoreStatus').html('<span class="badge badge-danger">name not unique</span>');
                            }
                        },
                        error: function(response){
                            console.log(response);
                        }
                    });
                } else {
                    $('#viewStoreStatus').html('<span class="badge badge-danger">name empty</span>');
                }
            }
        
            function updateLeftMultiDrop() {
                $.ajax({
                    url: "http://www.joostverberk.nl/api/graph/sensors.php",
                    dataType:'json',
                    method: "POST",
                    data: {quantity_id: $('#LeftAxisDropdown').val(), user_id: '<?php echo $_SESSION['user_id'];?>'},
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
                    data: {quantity_id: $('#RightAxisDropdown').val(), user_id: '<?php echo $_SESSION['user_id'];?>'},
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
              var graph_date = $('#datepicker').data('datepicker').getFormattedDate('yyyy-mm-dd');
              console.log(left_axis,right_axis);
              renderChart(left_axis,right_axis,graph_date);
            }
            
            setInterval(function() {
                updateGraph();
            }, 300 * 1000); // x * ms
        </script>
	</body>
</html>