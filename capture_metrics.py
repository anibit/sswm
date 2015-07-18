# Website performance testing script
# Copyright 2014 Jon Wolfe/Anibit Technology All rights reserved.
# You may use this script as you see fit, but you may not claim 
# credit for it's authorship.
# If you do find this useful, a note to anibit.technology@gmail.com would 
# be greatly appreciated.

#This was originaly wirtten using Python 3.4
#This script is meant to be rude, crude, and obnoxious. It will work for you.

import json
import minify_json
import re
import os
import sqlite3
import time
import datetime
import random

from subprocess import call

scriptVersion = 1

minimumDBSchema = scriptVersion

#database access

def setup_database(db_name, enable_db_reset):
    version = minimumDBSchema
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM version")
            result = cursor.fetchone()
            version = result[0]
            print (version)
    except sqlite3.OperationalError as e:
        version = -1
    if version < minimumDBSchema and enable_db_reset:
        create_new_db(db_name)
    return sqlite3.connect(db_name)


#create new DB

def create_new_db(filename):
    with sqlite3.connect(filename) as conn:
        cursor = conn.cursor()

        #create meta table
        cursor.execute("DROP TABLE IF EXISTS version")
        cursor.execute("CREATE TABLE version (versionID INTEGER)")
        #add version information
        cursor.execute("INSERT INTO version VALUES (" + str(scriptVersion) + ")");

        cursor.execute("DROP TABLE IF EXISTS timings")
        cursor.execute("DROP TABLE IF EXISTS urls")
        cursor.execute("DROP TABLE IF EXISTS jobruns")

        #create jobruns table
        cursor.execute("CREATE TABLE jobruns (id INTEGER PRIMARY KEY, date DATETIME, tot_runtime_sec real)")

        #create urlstable
        cursor.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT)")

        #create timing entries
        cursor.execute("CREATE TABLE timings (id INTEGER PRIMARY KEY, run_id INTEGER, url_id INTEGER, time_to_first_data real, load_time_sec real, FOREIGN KEY(run_id) REFERENCES jobruns(id), FOREIGN KEY(url_id) REFERENCES urls(id) )")

    cursor.execute("CREATE INDEX [index_id_run_id] ON [timings] ( [run_id] ASC);")
    cursor.execute("CREATE INDEX [index_id_url_id] ON [timings] ([url_id] ASC);")

def db_log_job_runs(db_connection):
    cursor =  db_connection.cursor()
    now = datetime.datetime.utcnow()


    #for debugging, randomize days into the past COMMENT THIS OUT!
    #now = now - datetime.timedelta(days = random.randint(0, 30))

    cursor.execute ("INSERT INTO jobruns(date, tot_runtime_sec) VALUES (?, ?)", (now, -1))
    id = cursor.lastrowid
    db_connection.commit()
    return id

def db_log_main_run_time(db_connection, job_run_id, run_time):
    cursor = db_connection.cursor()
    cursor.execute("UPDATE jobruns SET tot_runtime_sec=? WHERE id=?", (run_time, job_run_id))
    db_connection.commit()


def db_get_url_id(db_connection, url):
    cursor = db_connection.cursor()
    cursor.execute ("SELECT * FROM urls WHERE url = ?", (url,))
    result = cursor.fetchone()

    if result is None:
        cursor.execute("INSERT INTO urls(url) VALUES (?)", (url,))
        db_connection.commit()
        return cursor.lastrowid

    return result[0]

def db_log_job(db_connection, main_run_id, url, timeToFirstData, totalTime):
    url_id = db_get_url_id(db_connection, url)
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO timings(run_id, url_id, time_to_first_data, load_time_sec) VALUES (?, ?, ?, ?)", 
                   (main_run_id, url_id, timeToFirstData, totalTime))
    db_connection.commit()


timestampRegexString = r"^([0-1][0-9]|[2][0-3]):([0-5][0-9]):([0-5][0-9])\.([0-9]+)"

def get_time(text):
    regex = re.match(timestampRegexString, text)
    timeInSeconds = int(regex.group(1)) * 3600 + int(regex.group(2)) * 60 + float(regex.group(3) + "." + regex.group(4))
    return timeInSeconds
    

def parse_timings(filename):
    with open(filename) as f:
        lines = f.readlines()
    linesWithTimings = [ l for l in lines if re.match(timestampRegexString, l)]

    linesWithInfoconnected = [ l for l in linesWithTimings if re.match(r".*==\sInfo:\sConnected\sto.*", l)]

    linesWithInfoConnLeftIntact = [ l for l in linesWithTimings if re.match(r".*==\sInfo:\sConnection.*", l)]

    linesWithRecvData = [ l for l in linesWithTimings if re.match(r".*<=\sRecv\sdata.*", l)]


    startTime = get_time(linesWithInfoconnected[0])
    endTime = get_time(linesWithInfoConnLeftIntact[0])
    ttfdb = get_time(linesWithRecvData[0])

    totalTime = endTime - startTime
    #if the result is negative, we crossed a day boundary
    if totalTime < 0:
        totalTime = totalTime + 24*3600

    timeToFirstDataByteTime = ttfdb - startTime

    if timeToFirstDataByteTime < 0:
        timeToFirstDataByteTime = timeToFirstDataByteTime + 24*3600

    return (timeToFirstDataByteTime, totalTime)


def run_job(db_connection, config, url, main_run_id):
    curlPath = config['curl_path']
    curlOptions = "-k --trace-ascii timings.txt --trace-time"
    with open(os.devnull, 'w') as devnull:
        call(curlPath + " " + curlOptions + " " + url, stdout= devnull)
    (timeToFirstData, totalTime) = parse_timings("timings.txt")
    db_log_job(db_connection, main_run_id, url, timeToFirstData, totalTime)
    print ("url: " + url)
    print ("\ttime: " + str(totalTime) + " seconds")


def run_main_job():
    startTime = datetime.datetime.utcnow()

    print ("Anibit website timer, (c) 2014-2015 Anibit Technology");
    print ("Reading config...")
    with open("capture_metrics.config.json") as f:
        minified = minify_json.json_minify(f.read())
        config = json.loads(minified)

    #check to see if there is a valid database already
    dbConnection = setup_database(config['db_name'], config['enable_db_reset'])

    jobRunID = db_log_job_runs(dbConnection)

    #get list of URL's
    for urlJob in config['url_jobs']:
        run_job(dbConnection, config, urlJob['url'], jobRunID)

    endTime = datetime.datetime.utcnow()

    delta = endTime - startTime

    db_log_main_run_time(dbConnection, jobRunID, delta.total_seconds())

    print ("complete.")
    

if __name__ == "__main__":
    random.seed()
    run_main_job()
