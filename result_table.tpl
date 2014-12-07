%# Website performance testing script
%# Copyright 2014 Jon Wolfe/Anibit Technology All rights reserved.
%# You may use this script as you see fit, but you may not claim 
%# credit for it's authorship. I request, but not require, that you 
%# retain the generated copyright notice in it's entirety in any metrics pages
%# 
%# If you do find this useful, a note to anibit.technology@gmail.com would 
%# be greatly appreciated.

%import datetime

<h2>Timings Table</h2>

<table>
	<tr>
		<th>Time</th><th>url</th><th>Time to Data</th><th>Total Time</th>
	</tr>
	%for timing in timings:
		<tr>
			<td>{{datetime.datetime.strptime(timing[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")}}</td>
			<td><a href="{{timing[1]}}">{{timing[1]}}</a></td>
			<td style="text-align:right">{{"{:.3f}".format(timing[2])}}</td>
			<td style="text-align:right">{{"{:.3f}".format(timing[3])}}</td>
		</tr>
	%end

</table>