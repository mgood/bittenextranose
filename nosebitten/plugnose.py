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
# Patched by Kevin Tran on December 28, 2012 to update the usage of the Nose API and provide the duration (in seconds) each test ran for.

import os
import logging
import time
import traceback
from cStringIO import StringIO
from nose.plugins.base import Plugin
from nose.plugins.cover import Coverage
from nose.util import test_address
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
            metavar='FILE',
            help='write XML test results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'test-results.xml')
        )

    def configure(self, options, conf):
        log.debug('Configuring Bitten plug')
        Plugin.configure(self, options, conf)
        self.options = options
        self.conf = conf

    def begin(self):
        log.debug('Starting Bitten Output')
        if not os.path.exists(os.path.dirname(self.options.xml_results)):
            os.makedirs(os.path.dirname(self.options.xml_results))
        self.dom = xmlio.Element('unittest-results')

    def _add_test_result(self, test, status, output, duration, err=None):
        filename, module, _ = test_address(test)
        if filename and (filename.endswith('.pyc') or
                         filename.endswith('.pyo')):
            filename = filename[:-1]
        name = str(test)
        fixture = module or test.id()
        description = test.shortDescription() or ''
        case = xmlio.Element('test', file=filename, name=name, fixture=fixture,
                             status=status, duration=duration)
        if description:
            case.append(xmlio.Element('description')[description])
        if output:
            case.append(xmlio.Element('stdout')[output])
        if err is not None:
            tb = traceback.format_exception(*err)
            case.append(xmlio.Element('traceback')[tb])
        self.dom.append(case)

    def addError(self, test, err):
        duration = time.time() - self.before_time
        self._add_test_result(test.test, 'error', test.capturedOutput, duration, err)

    def addFailure(self, test, err):
        duration = time.time() - self.before_time
        self._add_test_result(test.test, 'failure', test.capturedOutput, duration, err)

    def addSuccess(self, test):
        duration = time.time() - self.before_time
        self._add_test_result(test.test, 'success', test.capturedOutput, duration)

    def finalize(self, result):
        self.dom.write(open(self.options.xml_results, 'wt'), newlines=True)

    def beforeTest(self, test):
        self.before_time = time.time()


class BittenNoseCoverage(Coverage):
    name = 'bitten-coverage'

    def options(self, parser, env=os.environ):
        Coverage.options(self, parser, env)
        Plugin.add_options(self, parser, env)
        parser.add_option(
            '--coverage-summary', action='store', dest='coverage_summary',
            metavar='FILE',
            help='write XML coverage results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'coverage-results.txt'),
        )
        parser.add_option(
            '--cover-packages', action='store', dest='cover_packages',
            default=env.get('NOSE_COVER_PACKAGE'),
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
