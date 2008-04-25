# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id$
# =============================================================================
#             $URL$
# $LastChangedDate$
#             $Rev$
#   $LastChangedBy$
# =============================================================================
# Copyright (C) 2006 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
import os
import sys
import time
import logging
from cStringIO import StringIO
from nose.plugins.base import Plugin
from nose.plugins.cover import Coverage
from nose.util import tolist
from bitten.util import xmlio
from bitten.util.testrunner import filter_coverage


log = logging.getLogger('nose.plugins.nosebitten')


class BittenNosetests(Plugin):
    """
    Use this plugin to write XML output to be used by Bitten.
    """

    name = 'bitten'

    def add_options(self, parser, env=os.environ):
        log.debug('Adding options on Bitten plug')
        Plugin.add_options(self, parser, env)
        parser.add_option(
            '--xml-results', action='store', dest='xml_results',
            metavar='FILE', help='write XML test results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'test-results.xml')
        )

    def configure(self, options, conf):
        log.debug('Configuring Bitten plug')
        Plugin.configure(self, options, conf)
        self.options = options
        self.conf = conf

    def begin(self):
        self.dom = xmlio.Element('unittest-results')
        log.debug('Starting Bitten Output')
        if not os.path.exists(os.path.dirname(self.options.xml_results)):
            os.makedirs(os.path.dirname(self.options.xml_results))
        self.fpaths = {}
        self.fpath = None
        self.tests = {}

    def startTest(self, test):
        name = str(test)
        fixture = None
        description = test.shortDescription() or ''
        self.test = {}
        if description.startswith('doctest of '):
            name = 'doctest'
            fixture = description[11:]
            description = None
        elif description.startswith('Doctest: '):
            name = 'doctest'
            fixture = description
        else:
            match = re.match('(\w+)\s+\(([\w.]+)\)', name)
            if match:
                name = match.group(1)
                fixture = match.group(2)
        self.tests[str(test)] = {}
        if fixture:
            tpath = fixture.rsplit('.', 1)[0].replace('.', os.sep) + '.py'
            if tpath.startswith('Doctest: '):
                tpath = tpath[9:]

            if not os.path.isfile(os.path.join(os.getcwd(), tpath)):
                for sdir in ('test', 'tests', 'unittest', 'unitests'):
                    if os.path.isfile(os.path.join(os.getcwd(), sdir, tpath)):
                        tpath = os.path.join(sdir, tpath)
            self.tests[str(test)]['file'] = tpath
        self.tests[str(test)]['name'] = name
        self.tests[str(test)]['fixture'] = fixture
        self.tests[str(test)]['description'] = description

    def addError(self, test, err, capt):
        self.tests[str(test)]['status'] = 'error'
        self.tests[str(test)]['traceback'] = err
        self.tests[str(test)]['output'] = capt

    def addFailure(self, test, err, capt, tb_info):
        self.tests[str(test)]['status'] = 'failure'
        self.tests[str(test)]['traceback'] = tb_info
        self.tests[str(test)]['output'] = capt

    def addSuccess(self, test, capt):
        self.tests[str(test)]['status'] = 'success'
        self.tests[str(test)]['output'] = capt

    def stopTest(self, test):
        # Enclose in a try because the nose colector apears here
        try:
            if self.tests[str(test)].has_key('status'):
                case = xmlio.Element('test')
                for key, val in self.tests[str(test)].iteritems():
                    if val:
                        case.append(xmlio.Element(key)[val])
                self.dom.append(case)
        except KeyError:
            pass

    def finalize(self, result):
        self.dom.write(open(self.options.xml_results, 'wt'), newlines=True)


class BittenNoseCoverage(Coverage):
    name = 'bitten-coverage'

    def options(self, parser, env=os.environ):
        Coverage.options(self, parser, env)
        Plugin.add_options(self, parser, env)
        parser.add_option(
            '--coverage-summary', action='store', dest='coverage_summary',
            metavar='FILE', help='write XML coverage results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'coverage-results.txt')
        )
        parser.add_option(
            '--cover-packages', action='store', default=env.get('NOSE_COVER_PACKAGE'), dest='cover_packages'
        )

    def configure(self, options, config):
        Coverage.configure(self, options, config)
        self.coverage_summary = options.coverage_summary

    def begin(self):
        if not os.path.exists(os.path.dirname(self.coverage_summary)):
            os.makedirs(os.path.dirname(self.coverage_summary))
        Coverage.begin(self)

    def report(self, stream):
        buf = StringIO()
        Coverage.report(self, buf)
        buf.seek(0)
        fileobj = open(self.coverage_summary, 'w')
        try:
            filter_coverage(buf, fileobj)
        finally:
            fileobj.close()
        buf.seek(0)
        stream.writelines(buf)
