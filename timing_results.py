# Website performance testing script
# Copyright 2014 Jon Wolfe/Anibit Technology All rights reserved.
# You may use this script as you see fit, but you may not claim 
# credit for it's authorship. I request, but not require, that you 
# retain the generated copyright notice in it's entirety in any metrics pages
# 
# If you do find this useful, a note to anibit.technology@gmail.com would 
# be greatly appreciated.

#This was originally written using Python 3.4
#This script is meant to be rude, crude, and obnoxious. It will work for you.

from bottle import route, post, run, template, request, static_file
import datetime
import sqlite3
import json
import minify_json

config = {}



def query_data():
    #figure out our parameters
    toTime = request.query.to_time

    if len(toTime) == 0:
        toTime = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    toTimeDate = datetime.datetime.strptime(toTime, "%Y-%m-%d") #kludgy way to strip time by reparsing the date-only string, don't judge

    fromTime = request.query.from_time
    if len(fromTime) == 0:
        fromTime = (toTimeDate - datetime.timedelta(7) ).strftime("%Y-%m-%d")

    fromTimeDate = datetime.datetime.strptime(fromTime, "%Y-%m-%d") #kludgy way to strip time by reparsing the date-only string, don't judge

    #we want up until the last second of the upper bound day, so add some time.
    toTimeDate = toTimeDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)

    #figure out any filter values
    if 'filter' in request.query.dict:
        filter = request.query.dict['filter']
        filterIDs = [x for x in filter if x != -1]
    else:
        filterIDs = [];

    includeTable = request.query.include_table

    if len(includeTable) == 0:
        addTable = False
    else:
        addTable = (int(includeTable) == 1)

    excludeTimeoutStr = request.query.exclude_timeouts

    if len(excludeTimeoutStr) == 0:
        excludeTimeouts = False
    else:
        excludeTimeouts = (int(excludeTimeoutStr) == 1)

    #now do databasey stuff. 
    db_connection = sqlite3.connect(config['db_name'])

    cursor = db_connection.cursor()
    cursor.execute(r"SELECT * FROM jobruns WHERE datetime(date) >= datetime(?) AND datetime(date) <= datetime(?)", (fromTimeDate, toTimeDate))
    runs = cursor.fetchall()

    if len(filterIDs) > 0:
        extraFilter = "AND url_id in (%s)" % (",".join([str(x) for x in filterIDs]))
    else:
        extraFilter = ""

    if  excludeTimeouts:
        timeoutFilter = "AND timed_out == 0"
    else:
        timeoutFilter = ""


    query = "SELECT * FROM timings WHERE run_id IN (%s) %s %s" % (",".join([str(x[0]) for x in runs]), extraFilter, timeoutFilter)
    cursor.execute(query)
    timings = cursor.fetchall()

    
    url_ids = list(set([x[2] for x in timings])) #hack to limit to unique items
    #now get actual urls
    query = "SELECT * FROM urls WHERE id in (%s)" % ",".join([str(x) for x in url_ids])
    cursor.execute(query)

    url_results = cursor.fetchall()

    query = "SELECT * FROM urls"
    cursor.execute(query)
    all_url_results = cursor.fetchall()
    all_urls = dict( [ (x[0], x[1]) for x in all_url_results]) #make it into a dictionary.

    return timings, runs, url_results, all_urls, filterIDs, addTable, excludeTimeouts, fromTime, toTime

#todo consider using a template for this stuff...
def html_header():
    return '''<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>Stupid Simple Website Metrics</title>
        <style>
        table, th, td {
            border: 1px solid black;
        }
        h1 { 
            float: left; 
        }
        </style>
    </head>
    <body>
    <div style="overflow: hidden;">
        <span>
            <h1>Stupid Simple Website Metrics</h1>
            <a href="#copyright">(copyright)</a>
        </span>
    </div>
    '''
def html_footer():
    return '''
        <br><br>
        <span id = "copyright">Metrics generated by: <br> <strong>Stupid Simple Website Metrics (C)2014-2015 by <a href="http://www.bytecruft.com">Jon Wolfe</a>/
        <a href="https://anibit.com">Anibit Technology LLC</a></strong>
        <br><br>
        See the <a href="http://github.com/anibit/sswm">Project Page on GitHub</a> for more information.
        </span>
        </body>
    </html>
    '''


@route('/')
def root():

    (timings, runs, url_results, all_urls, filterIDs, addTable, excludeTimeouts, fromTime, toTime) = query_data()
    #massage the data to the form we want it for tables

    urls = dict( [ (x[0], x[1]) for x in url_results ]) #make a dictionary of ids -> url string
    run_dates = dict( [(x[0], x[1]) for x in runs]) # make a dictionary of run ids -> run job time
    timing_data = sorted([ (run_dates[x[1]], urls[x[2]], x[3], x[4], x[5]) for x in timings], key = lambda x: x[0])

    chart_timing_data = [ 
                        (url,
                         sorted([(run_dates[t[1]], t[3], t[4], t[5]) for t in timings if url_id == t[2]], key = lambda x: x[0])
                         ) 
                         for (url_id, url) in urls.items()]

    #now generate some html to display it.
    #allow all urls in the db to appear in the filter

    url_filter_items = "".join(["<input type=\"checkbox\" name=\"filter\" value=\"" 
                                 + str(url_id) + "\"" + (" checked" if ((len(filterIDs) == 0) or (str(url_id) in filterIDs)) else "") 
                                 + ">" + url + "<br>" for (url_id, url) in all_urls.items()])

    include_table_filter_check = ("<input type=\"checkbox\" name=\"include_table\" value=\"1\"" + (" checked" if addTable else "") + "> Include Detail Table<br>") if config['display_table'] else ""
    include_timeouts_filter_check = ("<input type=\"checkbox\" name=\"exclude_timeouts\" value=\"1\"" + (" checked" if excludeTimeouts else "") + "> Exclude Timeouts <br>") 
    result = html_header() + '''
        <button  id="togglefilterbutton" onClick="toggleFilter()">Show Filter</button>
        <div id="filterexpanderdiv" style="display:none;">
            <h3>Filter</h3>
            <form id="filter_form_id" action="/" method="get">
                From: <input name="from_time" type = "date" value="%s"></input>
                To: <input name="to_time" type = "date" value="%s"></input>
                <br>
                Filter: <br>
                    %s                    
                    %s
                    %s
                <input type="submit" Value="refresh"></input>
            </form>
        </div>
        <script>
            ( function() {
                if (!sessionStorage.getItem('expandedFilter')) {
                    sessionStorage.setItem('expandedFilter', 0);
                }
                var expanded = sessionStorage.getItem('expandedFilter');
	            var div = document.getElementById("filterexpanderdiv");
	            var button = document.getElementById("togglefilterbutton");
	            if(expanded == 1) {
		            div.style.display = "block";
		            button.innerHTML = "Hide Filter";
  	            }
	            else {
    		        div.style.display = "none";
		            button.innerHTML = "Show Filter";
	            }                
            })();

            

            var toggleFilter = function() {
	            var div = document.getElementById("filterexpanderdiv");
	            var button = document.getElementById("togglefilterbutton");
	            if(div.style.display == "block") {
    		        div.style.display = "none";
		            button.innerHTML = "Show Filter";
                    sessionStorage.setItem('expandedFilter', 0);
  	            }
	            else {
		            div.style.display = "block";
		            button.innerHTML = "Hide Filter";
                    sessionStorage.setItem('expandedFilter', 1);
	            }                
            };
        </script>
        ''' % (fromTime, toTime, url_filter_items, include_table_filter_check, include_timeouts_filter_check )

    result += template("chart", timings = chart_timing_data)

    if config['enable_spreadsheet']:
        result += '''
        <iframe name="download_hidden_frame" style="display:none;"></iframe>
        <button type="submit" form="filter_form_id" formtarget="download_hidden_frame" formaction="spreadsheet" >Download Spreadsheet</button>
        <script>
        </script>
        '''

    if config['display_table'] and addTable:
        result += template("result_table", timings = timing_data)
    
    result = result +  html_footer()

    return result

@route('/spreadsheet')
def route_spreadsheet():
    global config
    if not config['enable_spreadsheet']:
        return '''
    <html>
<head>
</head>
<body>
<script>
    alert('Spreadsheets not enabled on your server, check your config');
</script>
</body>
</html>'''
    else:
        try:
            from timing_result_spreadsheet import generate_spreadsheet
        except ImportError:
            return '''
    <html>
<head>
</head>
<body>
<script>
    alert('The server is missing the needed python module to make spreadsheets, install "XlsxWriter"');
</script>
</body>
</html>
            '''

        (timings, runs, url_results, all_urls, filterIDs, addTable, excludeTimeouts, fromTime, toTime) = query_data()
        return generate_spreadsheet(config, timings, runs, url_results, all_urls, filterIDs, addTable, excludeTimeouts, fromTime, toTime)

@route('/static/<filename:path>')
def route_static_files_cb(filename):
    return static_file(filename, "./static")

@route('/temp/<filename:path>')
def temp_file_router(filename):
    return static_file(filename, config['temp_public_path'], download=filename)

def run_server():
    global config
    print ("Anibit website timer results server, (c) 2014-2015 Anibit Technology");
    print ("Reading config...")
    with open("timing_results.config.json") as f:
        minified = minify_json.json_minify(f.read())
        config = json.loads(minified)
    print ("starting server...")
    run(host=config['server_host'], port = config['server_port'], debug=True)


if __name__ == "__main__":
    run_server()
