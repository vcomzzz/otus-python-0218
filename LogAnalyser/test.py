#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Check that log_analyzer creates correct table from artificial log-file,
using test configuration, and render result into the simplest template
The essense of test is the comarison ethalon proper_table vs result of log_analyzer.py
'''


import unittest
import json
import os
import subprocess


proper_table = \
[ { 'url': 'GET url1',
    'count': 4,
    'count_perc': 25.0,
    'time_max': 4.0,
    'time_sum': 10.0,
    'time_med': 2.5,
    'time_perc': 34.5,
    'time_avg': 2.5 },
  { 'url': 'GET url4',
    'count': 4,
    'count_perc': 25.0,
    'time_max': 2.5,
    'time_sum': 8.0,
    'time_med': 2.0,
    'time_perc': 27.6,
    'time_avg': 2.0} ]


class AnalyzerTestCase(unittest.TestCase):
    def setUp(self):
        self.res_file = "./test/report-2018.01.01.html"

        with open('./test/config.json') as json_file:
            self.conf = json.load(json_file)

        subprocess.check_output('./log_analyzer.py --config=./test/config.json', shell=True)
        with open(self.res_file, 'rt') as rf:
            self.jres = json.loads(rf.read())

    def tearDown(self):
        os.remove(self.res_file)
        os.remove(self.conf["LOGGING"])
        os.remove(self.conf["TS"])

    def runTest(self):
        self.assertEqual(len(proper_table), len(self.jres), msg='different table lenght')
        for rp, rt in zip(proper_table, self.jres):
            for k, v in rp.items():
                self.assertIn(k, rt, msg='table does not contain ' + k)
                if not k == 'url':
                    self.assertAlmostEqual(float(rp[k]), float(rt[k]), delta=0.1, msg='incorrect '+ k)
                else:
                    self.assertEqual(rp[k], rt[k], msg='different urls were chosen')

if __name__ == '__main__':
    unittest.main()
