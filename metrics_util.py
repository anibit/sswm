
import datetime

def get_time_struct(string):
    if "." in string:
        string, frac = string.split(".")
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

