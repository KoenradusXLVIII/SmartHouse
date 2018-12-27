$(document).ready(function(){
	renderChart(3,4)
});

function renderChart(leftAxis, rightAxis) {
    $.ajax({
    	url: "http://www.joostverberk.nl/api/graph/data.php?leftAxis=" + leftAxis + "&rightAxis=" + rightAxis,
    	method: "GET",
    	success: function(data) {
    		console.log(data);
    		var timestamp = [];
    		var left = [];
    		var right = [];
    		var url = "http://www.joostverberk.nl/api/graph/data.php?leftAxis=" + leftAxis + "&rightAxis=" + rightAxis;
    
    		for(var i in data) {
    			if(data[i].sensor_id==leftAxis) {
    			    timestamp.push(data[i].timestamp);
    			    left.push(data[i].value);
    			    left_quantity = data[i].quantity_name;
    			    left_sensor = data[i].sensor_name;
    			    left_uom = data[i].uom;
    			}
    			if(data[i].sensor_id==rightAxis) {
    			    right.push(data[i].value);
    			    right_quantity = data[i].quantity_name;
    			    right_uom = data[i].uom;
    			    right_sensor = data[i].sensor_name;
    			}
    		}
    
            var ctx = $("#graph-canvas");
    		var config = {
    			type: 'line',
    			data:
    			{
    			    labels: timestamp,
    			    datasets:
    			    [{
    				    label: left_sensor,
    				    fill: false,
    				    pointRadius: 0,
    				    borderColor: "#c45850",
    				    backgroundColor: "#c45850",
    				    data: left,
    				    yAxisID: 'y-axis-1'
    			    },
    			    {
    				    label: right_sensor,
    				    fill: false,
    				    pointRadius: 0,
    				    borderColor: "#3e95cd",
    				    backgroundColor: "#3e95cd",
    				    data: right,
    				    yAxisID: 'y-axis-2'
    			    }
    			    ]
    			},
    			options: {
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
                        yAxes: [{
                            id: 'y-axis-1',
                            position: 'left',
                            scaleLabel: {
                                display: true,
                                labelString: left_quantity + " [" + left_uom + "]",
                            },
                            ticks: {
                                callback: function(value, index, values) {
                                    return value + left_uom;
                                }
                            }
                        },{
                            id: 'y-axis-2',
                            position: 'right',
                            scaleLabel: {
                                display: true,
                                labelString: right_quantity + " [" + right_uom + "]",
                            },
                            ticks: {
                                callback: function(value, index, values) {
                                    return value + right_uom;
                                }
                            }
                        }
                        ]
                    }
                }
    		};
    		var lineGraph = new Chart(ctx, config);
    	}
    });
}