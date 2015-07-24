import xlsxwriter
import tempfile
import datetime
import io
import sys
from bottle import HTTPResponse
from os import path
import metrics_util

def generate_spreadsheet(config, timings, runs, url_results, all_urls, filterIDs, addTable, excludeTimeouts, fromTime, toTime):
    try:
        urls = dict( [ (x[0], (x[1], x[2])) for x in url_results ]) #make a dictionary of ids -> url/nickname
        run_dates = dict( [(x[0], x[1]) for x in runs]) # make a dictionary of run ids -> run job time
        timing_data = sorted([ (run_dates[x[1]], urls[x[2]], x[3], x[4], x[5]) for x in timings], key = lambda x: x[0])

        per_site_timing_data = [ 
                            (url[0], url_id, url[1],
                             sorted([(run_dates[t[1]], t[3], t[4], t[5]) for t in timings if url_id == t[2]], key = lambda x: x[0])
                             ) 
                             for (url_id, url) in urls.items()]

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory' : True}) 
        workbook.set_properties( {
            'title' : 'Website metrics from %s to %s' % (str(fromTime), str(toTime)),
            'author' : 'Jon Wolfe/Anibit Technology , LLC',
            'comments' : 'created by Stupid Simple Website Metrics http://anibit.com',
            })
        #tempfilename =  next(tempfile._get_candidate_names()) + ".xlsx"
        #temppath = path.join( config['temp_public_path'], tempfilename)
        #workbook = xlsxwriter.Workbook(temppath, {'in_memory' : True})
        #date_format = workbook.add_format({'num_format': 'dd/mm/yy hh:mm:ss'})
        date_format = workbook.add_format({'num_format': 'mmm d yyyy hh:mm:ss AM/PM'})
        bad_timing_format = workbook.add_format({'font_color': '#FF0000'})
        timing_format = workbook.add_format({'num_format': '0.000'})
        slow_outlier_format = workbook.add_format({'bg_color' : 'FFAAAA'})
        fast_outlier_format = workbook.add_format({'bg_color' : 'AAFFAA'})
        if addTable or True:
            for ( url_name, url_id, url_nickname, site_timings) in per_site_timing_data:
                persite_worksheet = workbook.add_worksheet(url_nickname)
                persite_worksheet.set_column(0, 0, 25)
                persite_worksheet.set_column(1, 1, 15)
                persite_worksheet.set_column(2, 2, 15)
                persite_worksheet.set_column(3, 3, 15)
                persite_worksheet.set_column(4, 4, 20)
                persite_worksheet.write('A1', 'Url:')
                persite_worksheet.write('B1', url_name)
            
                persite_worksheet.write('A2', "Time") 
                persite_worksheet.write('B2', "Time to Data (seconds)") 
                persite_worksheet.write('C2', "Total Time") 
                persite_worksheet.write('D2', "Download Time")
                row_index = 6
                for site_timing in site_timings:
                    row_str = str(row_index + 1)
                    timestamp = metrics_util.get_time_struct (site_timing[0]) 
                    persite_worksheet.write_datetime( row_index, 0 , timestamp , date_format )
                    if (int(site_timing[3]) == 0):
                        persite_worksheet.write_number( row_index, 1 , site_timing[1], timing_format )
                        persite_worksheet.write_number( row_index, 2 , site_timing[2], timing_format )
                        persite_worksheet.write_formula( row_index, 3 , "=C" + row_str + "-B" + row_str, timing_format)
                    else:
                        persite_worksheet.write_string( row_index, 4, "TIMED OUT", bad_timing_format)                

                    row_index = row_index + 1



                persite_worksheet.write('A3', "Average");
                persite_worksheet.write_formula('B3', '=AVERAGE(B7:B' + row_str + ')', timing_format)
                persite_worksheet.write_formula('C3', '=AVERAGE(C7:C' + row_str + ')', timing_format)
                persite_worksheet.write_formula('D3', '=AVERAGE(D7:D' + row_str + ')', timing_format)

                persite_worksheet.write('A4', "Deviation");
                persite_worksheet.write_formula('B4', '=STDEV(B7:B' + row_str + ')', timing_format)
                persite_worksheet.write_formula('C4', '=STDEV(C7:C' + row_str + ')', timing_format)
                persite_worksheet.write_formula('D4', '=STDEV(D7:D' + row_str + ')', timing_format)

                persite_worksheet.write('A5', "Worst");
                persite_worksheet.write_formula('B5', '=MAX(B7:B' + row_str + ')', timing_format)
                persite_worksheet.write_formula('C5', '=MAX(C7:C' + row_str + ')', timing_format)
                persite_worksheet.write_formula('D5', '=MAX(D7:D' + row_str + ')', timing_format)

                persite_worksheet.write('A6', "Best");
                persite_worksheet.write_formula('B6', '=MIN(B7:B' + row_str + ')', timing_format)
                persite_worksheet.write_formula('C6', '=MIN(C7:C' + row_str + ')', timing_format)
                persite_worksheet.write_formula('D6', '=MIN(D7:D' + row_str + ')', timing_format)

                persite_worksheet.conditional_format('B7:B' + row_str + ')', {'type':     'cell',
                                            'criteria': '==',
                                            'value':    0.0,
                                            'format':   bad_timing_format})

                persite_worksheet.conditional_format('C7:C' + row_str + ')', {'type':     'cell',
                                'criteria': '==',
                                'value':    0.0,
                                'format':   bad_timing_format})


                persite_worksheet.conditional_format('B7:D' + row_str + ')', {'type':     'cell',
                                            'criteria': '>=',
                                            'value':    'B$3+B$4',
                                            'format':   slow_outlier_format})

                persite_worksheet.conditional_format('B7:D' + row_str + ')', {'type':     'cell',
                                            'criteria': '<=',
                                            'value':    'B$3-B$4',
                                            'format':   fast_outlier_format})


                #persite_worksheet.conditional_format('C7:C' + row_str + ')', {'type':     'cell',
                #                            'criteria': '>=',
                #                            'value':    'C3+C4',
                #                            'format':   slow_outlier_format})

                #persite_worksheet.conditional_format('C7:C' + row_str + ')', {'type':     'cell',
                #                            'criteria': '<=',
                #                            'value':    'C3-C4',
                #                            'format':   fast_outlier_format})


                #persite_worksheet.conditional_format('D7:D' + row_str + ')', {'type':     'cell',
                #                            'criteria': '>=',
                #                            'value':    'D3+D4',
                #                            'format':   slow_outlier_format})

                #persite_worksheet.conditional_format('D7:D' + row_str + ')', {'type':     'cell',
                #                            'criteria': '<=',
                #                            'value':    'D3-D4',
                #                            'format':   fast_outlier_format})


                persite_worksheet.freeze_panes(6, 0)

        workbook.close()
        xlsx_data = output.getvalue()

        headers = dict()
        headers['Content-Disposition'] = 'attachment; filename="sswm_from_%s_to_%s.xlsx"' % (fromTime, toTime)
        headers['Accept-Ranges'] = 'bytes'
        headers['Content-Type'] = 'application/vnd.ms-excel'

        return HTTPResponse(xlsx_data, **headers)
    except:
        e = sys.exc_info()
        a = e
        return '''
    <html>
<head>
</head>
<body>
<p>something went wrong</p>
<p>Stack trace:</p>
<p>%s</p>
<script>
    alert('There was a problem creating the spreadsheet');
</script>
</body>
</html>

        ''' % e

#    return '''
#    <html>
#<head>
#<meta http-equiv="Refresh" content="0; url=../temp/%s" />
#</head>
#<body>
#<p>downloading spreadsheet</p>
#</body>
#</html>
#    ''' % tempfilename