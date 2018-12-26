$(document).ready(function(){
	$.ajax({
		url: "http://www.joostverberk.nl/api/graph/data.php",
		method: "GET",
		success: function(data) {
			console.log(data);
			var timestamp = [];
			var temp = [];
			var humi = [];

			for(var i in data) {
				if(data[i].sensor_id==3) {
				    timestamp.push(data[i].timestamp);
				    temp.push(data[i].value);
				}
				if(data[i].sensor_id==4) {
				    humi.push(data[i].value);
				}
			}


			var ctx = $("#mycanvas");
			var lineGraph = new Chart(ctx, {
				type: 'line',
				data:
				{
				    labels: timestamp,
				    datasets:
				    [{
    				    label: 'Temperature',
    				    fill: false,
    				    pointRadius: 0,
    				    borderColor: "#c45850",
    				    data: temp,
    				    yAxisID: 'y-axis-1'
				    },
				    {
    				    label: 'Humidity',
    				    fill: false,
    				    pointRadius: 0,
    				    borderColor: "#3e95cd",
    				    data: humi,
    				    yAxisID: 'y-axis-2'
				    }
				    ]
				},
				options: {
				    legend: {
				        display: false
				    },
				    tooltips: {
						position: 'nearest',
						mode: 'index',
						intersect: false,
					},
                    responsive: false,
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
                                labelString: "Temperature [C]",
                            },
                            ticks: {
                                callback: function(value, index, values) {
                                    return value + 'C';
                                }
                            }
                        },{
                            id: 'y-axis-2',
                            position: 'right',
                            scaleLabel: {
                                display: true,
                                labelString: "Humidity [%]",
                            },
                            ticks: {
                                callback: function(value, index, values) {
                                    return value + '%';
                                }
                            }
                        }
                        ]
                    }
                }
			});
		},
		error: function(data) {
			console.log(data);
		}
	});
});