%# Website performance testing script
%# Copyright 2014 Jon Wolfe/Anibit Technology All rights reserved.
%# You may use this script as you see fit, but you may not claim 
%# credit for it's authorship. I request, but not require, that you 
%# retain the generated copyright notice in it's entirety in any metrics pages
%# 
%# If you do find this useful, a note to anibit.technology@gmail.com would 
%# be greatly appreciated.

%import datetime
%import metrics_util

<script src="/static/flot/jquery.min.js"></script>
<script src="/static/flot/jquery.flot.min.js"></script>
<script src="/static/flot/jquery.flot.time.min.js"></script>
<style>
table.chart_table, th.chart_table, td.chart_table {
            border: 0
</style>
<h2>Timings Chart</h2>

<table class="chart_table" style="border:0">
	<tr class="chart_table"><td class="chart_table">
		<div id="timingsChart" style="width:900px;height:400px;float:left"></div>
		<div id="legend" style="float:left"></div>
	</td></tr>
</table>

<br>
<script>
	var data = [
	%for timing in timings:
		{
			label: "{{timing[0]}}",
			data: [
			%for p in timing[1]:
				[{{int(metrics_util.get_time_struct(p[0]).replace(tzinfo=datetime.timezone.utc).timestamp()*1000)}}, {{p[1]}}, {{p[2]}}, {{p[3]}}]
				%if p != timing[1][-1]: 
					,
				%end	
			%end
			],
			clickable: true,
			hoverable: true
		}
		%if timing != timings[-1]:
			,
		%end
	%end
	];

	var options = {
		series: {
			lines: { show: true },
			points: { show: true }
		},
		legend: {
			container : $("#legend")
		},
		grid: {
			hoverable: true
		},
		xaxis : {
			mode : "time",
			timeformat: "%Y-%m-%d %H:%M:%S"
		},
		yaxis : {
			show : true
		}
	};


	var plot = $("#timingsChart").plot(data, options);

	$("<div id='tooltip'></div>").css({
		position: "absolute",
		display: "none",
		border: "1px solid #fdd",
		padding: "2px",
		"background-color": "#efe",
		opacity: 0.80
	}).appendTo("body");

	$("#timingsChart").bind("plothover", function (event, pos, item) {

			if (item) {
				var x = item.datapoint[0].toFixed(2),
					y = item.datapoint[1].toFixed(2),
					y2 = item.series.data[item.dataIndex][2].toFixed(2),
					timeout = item.series.data[item.dataIndex][3];
				
				var numeric = parseFloat(x);
				var date = new Date(numeric);
				var dateString = date.toUTCString();
				if (timeout !== 1) {
					$("#tooltip").html(dateString + "<br>" +  "Time to data: <strong>" + y + "</strong> <br>Download time: <strong>" + (y2 - y).toFixed(2) +
						"</strong> <br>Total time: <strong>" + y2 +"</strong><br>(" + item.series.label + ")")
						.css({top: item.pageY+5, left: item.pageX+5, "background-color":item.series.color})
						.fadeIn(200);
				} else {
					$("#tooltip").html(dateString + "<br><strong>TIMED OUT</strong><br>(" + item.series.label + ")")
						.css({top: item.pageY+5, left: item.pageX+5, "background-color":item.series.color})
						.fadeIn(200);
					
				}
			} else {
				$("#tooltip").hide();
			}
	});


</script>

