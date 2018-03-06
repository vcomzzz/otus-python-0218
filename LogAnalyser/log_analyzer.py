#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

# 1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" "2a828197ae235b0b3cb" 0.70
# 1.141.86.192 -  - [29/Jun/2017:06:55:55 +0300] "GET /export/appinstall_raw/2017-06-29/ HTTP/1.0" 200 51236 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)" "-" "-" "-" 0.004

import logging
import json
import argparse
import sys
import os.path
import gzip
import glob
import re
import numpy as np
from string import Template
import heapq
import subprocess
import time
from collections import namedtuple


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "REPORT_TEMPLATE": "./report.html",
    "LOG_DIR": "./log",
    "LOGGING": None,
    "TS": "./log_analyzer.ts",
    "CRITICAL_PERC_ERR": 50,
}


def get_log_file(conf):
    LogFile = namedtuple('LogFile', 'path date')

    # find log to process
    all_logs = glob.glob(os.path.join(conf["LOG_DIR"], 'nginx-access-ui.log-*'))
    my_log = LogFile(None, 0)
    for lg in all_logs:
        dt = re.search('([0-9]+)(.gz){0,1}$', lg)
        if dt is not None:
            idt = dt.group(1)
            if int(idt) > int(my_log.date):
                my_log = LogFile(lg, idt)

    if my_log.path is None:
        logging.error('there are no propriate logs')
        sys.exit()
    else:
        logging.info('found apropriate log-file: ' + my_log.path)
    return my_log


def get_report_path(conf, my_log):
    rep_file = 'report-{}.{}.{}.html'.format(my_log.date[:4], my_log.date[4:6], my_log.date[6:])
    rep_path = os.path.join(conf["REPORT_DIR"], rep_file)

    if not os.path.exists(conf["REPORT_DIR"]):
        os.makedirs(conf["REPORT_DIR"])

    if os.path.isfile(rep_path):
        logging.info('report was already created: ' + rep_path)
        sys.exit()
    return rep_path


def log_line_parser(log_file):
    req_rec = re.compile('((GET|POST|HEAD)\s+\S+)\s+')
    time_rec = re.compile('\s+[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$')

    with gzip.open(log_file, 'rt') if log_file.endswith(".gz") else open(log_file) as fl:
        for line in fl:
            rs_rq = req_rec.search(line.strip())
            rs_tm = time_rec.search(line.strip())
            if rs_rq is None or rs_tm is None:
                yield None
            else:
                request = rs_rq.group(1)
                req_time = float(rs_tm.group(1))
                yield (request, req_time)


def get_critical_number_of_lines(my_log, conf):
    try:
        wc_com = 'gunzip -c {} | wc -l' if my_log.path.endswith(".gz") else 'wc -l {}'
        r = subprocess.check_output(wc_com.format(my_log.path), shell=True)
    except CalledProcessError:
        logging.error('cannot count the number of lines in the log')
        sys.exit()
    num_lines = int(r.decode().strip().partition(' ')[0])
    if not num_lines > 0:
        logging.error('there are no lines in log')
        sys.exit()
    return num_lines * conf["CRITICAL_PERC_ERR"] / 100.0


def log_parser(line_parser, conf, n_errs_critical):
    tmdata = {}
    sumtime = {}
    num_lines_good = 0
    n_errs = 0
    alltime = 0.00

    for line in line_parser:
        if line is None:
            n_errs += 1
            if n_errs > n_errs_critical:
                logging.error('too many incorrect lines in the log')
                sys.exit()
        else:
            request, req_time = line
            tmdata.setdefault(request, []).append(req_time)
            sumtime[request] = sumtime.get(request, 0.00) + req_time
            num_lines_good += 1
            alltime += req_time

    if not alltime > 0.00:
        logging.error('all times in the log equal to zero')
        sys.exit()

    # build report table
    urlviz = list(heapq.nlargest(conf["REPORT_SIZE"], sumtime.keys(), lambda x: sumtime[x]))
    rep_table = []
    for url in urlviz:
        tm = np.array(tmdata[url])
        rec = {"url": url,
               "count": tm.size,
               "count_perc": '{:.3f}'.format(100.0 * tm.size / num_lines_good),
               "time_sum":   '{:.3f}'.format(np.sum(tm)),
               "time_avg":   '{:.3f}'.format(np.average(tm)),
               "time_perc":  '{:.3f}'.format(100.0 * np.sum(tm) / alltime),
               "time_max":   '{:.3f}'.format(np.max(tm)),
               "time_med":   '{:.3f}'.format(np.median(tm))}
        rep_table.append(rec)
    return rep_table


def render_report(rep_table, conf):
    templ_file = conf["REPORT_TEMPLATE"]
    with open(templ_file, 'r') as tf:
        templ = tf.read()
    if len(templ) < 10:
        logging.error('incorrect template in ' + templ_file)
        sys.exit()
    return Template(templ).safe_substitute(table_json=json.dumps(rep_table))


def main(conf):
    logging.info('log_analyzer started with config: ' + str(conf))

    # find out log-file to parse
    my_log = get_log_file(conf)

    # get path to report in
    rep_path = get_report_path(conf, my_log)

    # find out the critical number of error lines
    n_errs_critical = get_critical_number_of_lines(my_log, conf)

    # parse log-file and build result table
    rep_table = log_parser(log_line_parser(my_log.path), conf, n_errs_critical)

    # render report
    report = render_report(rep_table, conf)

    # write report
    with open(rep_path, 'w') as rf:
        rf.write(report)

    logging.info('report created here: ' + rep_path)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    with open(conf["TS"], 'w') as tsf:
        tsf.write(timestr)


if __name__ == "__main__":
    conf = config
    comline_parser = argparse.ArgumentParser()
    comline_parser.add_argument('--config', help='external config', default='./config.json')
    args = comline_parser.parse_args()

    with open(args.config) as json_file:
        ext_config = json.load(json_file)
        conf = {**config, **ext_config}

    logging.basicConfig(format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S',
                        level=logging.INFO,
                        filename=conf["LOGGING"])
    try:
        main(conf)
    except:
        logging.exception()
