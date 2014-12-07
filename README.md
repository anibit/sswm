Stupid Simple Website Metrics
=============================

This is a tool for logging the overall performance of website over time.

It's written in Python and Javascript and is meant to be run from one machine to test the response time of another machine. It requires minimal setup beyond scheduling the metrics script (e.g. cron) and running the results views. Its only external dependency is [curl](http://curl.haxx.se/).


Overview
--------

The tool is made up of **two parts, the metrics collecting part, and the results viewer part**. Both are implemented in Python 3.4. The metrics collection application is meant to be run from a command-line, and uses a JSON based configuration file to control it's operation. The results viewer is a Python script that implements a web server you can point your browser to see the historic metrics data.

Getting started
---------------

###Installation


There isn't much to install. The two main Python scripts could be run from a command shell.


To capture metrics, run:

```
python capture_metrics.py```

To launch the web server for the results, run:

```
python timing_results.py```

There are no command line options, all configuration is done via **capture_metrics.config.json** and **timing_results.config.json**, for the metrics capture and results viewer, respectively.


Ideally, you want to capture metrics over time, the greatest power in this tool is doing historical trend analysis. ( *"Why is my site slow, when did it first get slow?*") To do this, you want to run the capture metrics script on a period basis. On Linux, you can schedule a cron task to do this. On Windows, you can use the "Scheduled Tasks" or "Task Scheduler", depending on what version of Windows you have. The period task needs to have the appropriate permissions to access external networks and to have read/write access to the "working directory" for access to the database, and to store temporary files while collecting metrics. 

The metrics web server is built using the [Bottle.py](http://bottlepy.org/) web micro framework for Python. Bottle is a WSGI-compliant very simple framework for building websites. The metrics viewer is designed to launch it's own simplistic internal server, but with a little modification it could run in your own server infrastructure.

The way that I run the metrics server is launch the script as a system service on Windows. This is fairly easy to do on Windows with [NSSM](http://nssm.cc/). On Linux or Mac, you would want to launch it as a daemon in your init scripts. These options are beyond the scope of these intructions, they are just ideas to get you started. 
  
###Configuration

The metrics capture is configured via the **capture_metrics.config.json** file. The following options are available:

| option        | description  |
| :------------:| ------------ |
| **curl_path** | The executable command used to launch curl<br>this can be left as is if curl is in your systems's path, <br>or resides in your script's working directory.         |
| **db_name**   | The name of the SQLite database used for storing <br>metrics. It will be created if it does not already exist |
| **enable_db_reset** | This allows the databse to be reset/cleared.<br> If the version a new version of the script requires a new<br> schema, this will detect it and re-create the database.<br>**THIS CAN WIPE OUT YOUR DATA,<br> SET TO '0' TO PROTECT IT** |
| **url_jobs** | This is a JSON array of objects containing the urls to test<br>They are objects s that options may be added in future<br>script versions |


The timing results server is configured via the **timing_results.config.json** file. The following options are available. 

| option        | description  |
| :------------:| ------------ |
| **server_host** | The host name used to start the Bottle.py server |
| **server_port** | The post name used to start the Bottle.py server |
| **db_name** | The nname of the database containing the metrics. <br> This must match what is used by the <br>metrics capture script. |
| **display_table** | Set to '1' to include the timings table in the output. <br> The timing table can get  lengthy, so this removes it. |

Viewing Metrics
---------------

Make sure the **timing_results.py** script is running, and point your browser to the machine and port. 

```
http://<your server>:<your port>
```

There are a couple of url parameters. This is useful is you want to create bookmarks to specific timings, or share particular views with others.

```
http://<your server>:<your port>/?from_time=<lower bound time>&to_time=<uppper bound time>&filter=<url id>
``` 

the from_time and to_time parameters let you specify the time span over which you wish to view metrics. Right now they are limit to whole days, and are based on UTC time. IT would be nice to make this a little more user friendly one day. The format for the time is:

```
[YYYY]-[MM]-[DD]
```

If the **to_time** parameter is missing, it is assumed to be "today"

If the **from_time** parameter is missing, it is assumed to be 30 days earlier than the **to_time**.

The filter parameter is based on the internal database ID of the URL. This is meant to be used by the form on the page, but the id should remain static, so that url ids can be used in bookmarks.

A filter ID of '-1' is a special ID that means "all urls for which there are metrics in the given time range".

An example url might look like:

```
http://metrics-server:8192/?from_time=2015-02-22&to_time=2015-02-28&filter=-1
```


Known Issues and Limitations
----------------
  * Metrics Capture
   * There are more metrics points that could be captured in the timings, such as SSL negotiation timings, header download timings, etc.
   * curl failures are not handled well, and may result in a partial metrics capture.
   * the timings are only of the time to serve the initial root document. This is a limitation of curl in that it does not recurse embedded links. Think of this as a server metrics tool, and not a general web page performance tool. (There are already a lot of good tools for that). If your site is heavily iframe-based, you may not capture all the relevent timings. Try using the urls within the iframes in that case. 
   * there is no facility for cleaning up of old entries. The database will grow forever. This may be addressed in the future.
  * Metrics Viewer 
   * The Date Picker is HTML5 and is not supported on all browsers, specifically Firefox does not support it. 
   * All times and dates are currently displayed in UTC/GMT. This is likely to be addressed in future versions.
   * The url filter resets to "(all urls)" on every refresh. This may or may not be fixed.
   * There is not a lot of attention paid to security. If you wish to run this as a publicly facing website, please, audit the code, (there is not a lot of it). If you spot any problems, let me know and I will incorporate it into a future version.
  * General
   * Python, Javascript, SQL, and HTML are not my native tongues as a developer. I come from a desktop and embedded development world using a lot of the _curly bracket_ languages. I speak Python and Javascript with a C#/C++/Java accent. If you see something in my code you think is horrendous from your experience as a seasoned web developer, enlightenment would be greatly appreciated.
   * I have only tested this on Windows, but I believe it ought to work on other platforms as well. If you are aware of issues on Linux or OSX, let me know, and I will merge in your changes.  
   * This tool was written to monitor the performance on my business's website, [Anibit Technology](https://anibit.com), which is built on PHP and Drupal.


Acknowledgments
----------------
This tool is made possible with the following:

  * [Python](https://www.python.org/)
  * [SQLite](http://www.sqlite.org/)
  * [Bottle.py](http://bottlepy.org/)
  * [JSON.minify.py](https://github.com/getify/JSON.minify)
  * [flot library](www.flotcharts.org)
  * [curl](http://curl.haxx.se/)
  * and copious visits to Stack Overflow

License
-------

Please see the LICENSE file for more info. 

I woudl like you to make use of this tool to help you. It would be cool if you dropped me a note at anibit.technology@gmail.com if you find it useful. Also I would appreciate it if you retained the copyright notice and links at the bottom of the generated output, but you are not required to do so. You may not, however, claim credit for authorship.   