$(document).ready(function(){
	renderChart([3],[4,9])
	$('#left_sensors').multiselect();
	$('#right_sensors').multiselect();
});

function renderChart(left_axis, right_axis) {
    //var jsonSensors = JSON.stringify(sensor_ids);
    $.ajax({
    	url: "http://www.joostverberk.nl/api/graph/data.php",
    	dataType:'json',
    	method: "POST",
    	data: {sensors: left_axis.concat(right_axis)},
    	success: function(data) {

            // Set colour sets
            var colorset = ["#003f5c","#7a5195","#ef5675","#ffa600"];

            // Set context
            var ctx = $("#graph-canvas");
            // Initialize config
    		var config = {
    		    type: 'line',
    		    data: {
    		        labels: [],
    		        datasets: []
    		    }
    		};

    		// Initialize options
    		var options = {
			    legend: {
			        display: true
			    },
			    tooltips: {
					position: 'nearest',
					mode: 'index',
					intersect: false,
				},
                responsive: true,
                scales: {
                    xAxes: [{
                        type: 'time',
                        time: {
                            unit: 'hour'
                        }
                    }],
                    yAxes: []
                }
    		};

    		// Initialize datasets in left axis
    		sensor_loop:
                for (var left_sensor_i = 0; left_sensor_i < left_axis.length; left_sensor_i++) {
            meas_loop:
                    for (var i1 in data) {
                        if(data[i1].sensor_id == left_axis[left_sensor_i]) {
                            if (left_sensor_i === 0) {
                                // Get axis information from first dataset
                                options.scales.yAxes.push({
                                    id: 'y-axis-1',
                                    position: 'left',
                                    scaleLabel: {
                                        display: true,
                                        labelString: data[i1].quantity_name + " [" + data[i1].uom + "]",
                                    },
                                    ticks: {
                                        callback: function(value, index, values) {
                                            return value + data[i1].uom;
                                        }
                                    }
                                });
                            }
                            // Get dataset information from each dataset
                            config.data.datasets.push({
                                label: data[i1].sensor_name,
                                fill: false,
                                pointRadius: 0,
    				            borderColor: colorset[left_sensor_i],
    				            backgroundColor: colorset[left_sensor_i],
    				            data: [],
    				            yAxisID: 'y-axis-1'
                            });
                            // Iterate to next sensor
                            break meas_loop;
                        }
                    }
                }

            // Initialize datasets in right axis
    		sensor_loop:
                for (var right_sensor_i = 0; right_sensor_i < right_axis.length; right_sensor_i++) {
            meas_loop:
                    for (var i2 in data) {
                        if(data[i2].sensor_id == right_axis[right_sensor_i]) {
                            if (right_sensor_i === 0) {
                                // Get axis information from first dataset
                                options.scales.yAxes.push({
                                    id: 'y-axis-2',
                                    position: 'right',
                                    scaleLabel: {
                                        display: true,
                                        labelString: data[i2].quantity_name + " [" + data[i2].uom + "]",
                                    },
                                    ticks: {
                                        callback: function(value, index, values) {
                                            return value + data[i2].uom;
                                        }
                                    }
                                });
                            }
                            // Get dataset information from each dataset
                            config.data.datasets.push({
                                label: data[i2].sensor_name,
                                fill: false,
                                pointRadius: 0,
    				            borderColor: colorset[left_axis.length + right_sensor_i],
    				            backgroundColor: colorset[left_axis.length + right_sensor_i],
    				            data: [],
    				            yAxisID: 'y-axis-2'
                            });
                            // Iterate to next sensor
                            break meas_loop;
                        }
                    }
                }

            // Attach options
            config.options = options;

            // Get timestamp information from first dataset
            for (var meas_id in data) {
                if(data[meas_id].sensor_id == left_axis[0]) {
                    config.data.labels.push(data[meas_id].timestamp);
                }
            }
            
            // Populate datasets with data
            all_sensors = left_axis.concat(right_axis);
            for (var i3 in data) {
                for (var all_sensor_i = 0; all_sensor_i < all_sensors.length; all_sensor_i++) {
                    if(data[i3].sensor_id == all_sensors[all_sensor_i]) {
                        config.data.datasets[all_sensor_i].data.push(data[i3].value);
                        break;
                    }
                }
            }

            console.log(config);

            // Draw chart
    		var lineGraph = new Chart(ctx, config);
    	},
    	error: function(response){
            console.log(response);
         }
    });
}