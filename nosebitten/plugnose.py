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
from nose.plugins.base import Plugin
from nose.util import tolist
from bitten.util import xmlio


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


class BittenNoseCoverage(Plugin):
    name = 'bitten-coverage'

    def add_options(self, parser, env=os.environ):
        Plugin.add_options(self, parser, env)
        parser.add_option(
            '--xml-coverage', action='store', dest='xml_coverage',
            metavar='FILE', help='write XML coverage results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'coverage-results.xml')
        )
        self.parser = parser

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        if self.enabled and not options.enable_plugin_coverage:
            self.parser.error('You need to enable coverage')
        self.conf = config
        self.options = options

    def begin(self):
        if not os.path.exists(os.path.dirname(self.options.xml_coverage)):
            os.makedirs(os.path.dirname(self.options.xml_coverage))
        self.skipModules = sys.modules.keys()[:]

    def report(self, stream):
        output = []
        class myfile(object):
            def write(self, towrite):
                output.append(towrite)
            def writelines(self, lines):
                output.extend(lines)

        import coverage
        modules = [ module
                    for name, module in sys.modules.items()
                    if self.wantModuleCoverage(name, module) ]
        coverage.report(modules, file=myfile(), show_missing=True)
        coverage_re = re.compile(
            r'(?P<mod>[\w\.]+)\s+(?P<lines>\d+)\s+(?P<exec>\d+)\s+'
            r'(?P<cover>\d+)%?\s+(?P<miss>[\d,\s-]+)'
        )
        root = xmlio.Element('coverage-results')
        for line in output:
            filename = None
            match = coverage_re.search(line)
            if match and line.find('TOTAL') == -1:
                module = match.group('mod')
                if os.path.isdir(os.path.join(os.getcwd(), module.replace('.', os.sep))):
                    mpath = os.path.join(
                        os.getcwd(),
                        module.replace('.', os.sep),
                        '__init__.py'
                    )
                    if os.path.isfile(mpath):
                        filename = mpath
                else:
                    if os.path.isfile(os.path.join(
                        os.getcwd(), module.replace('.', os.sep)+'.py')):
                        filename = os.path.join(
                            os.getcwd(), module.replace('.', os.sep)+'.py'
                        )
                lines = match.group('lines')
                hits = match.group('exec')
                cover = match.group('cover')
                if match.group('miss'):
                    miss = ''.join(match.group('miss').split(','))
                else:
                    miss = ''
                root.append(xmlio.Element(
                    'coverage', file=filename, name=module,
                    executed=hits, lines=lines, percentage=cover, miss=miss)
                )
        root.write(open(self.options.xml_coverage, 'w'), newlines=True)


    def wantModuleCoverage(self, name, module):
        if not hasattr(module, '__file__'):
            log.debug("no coverage of %s: no __file__", name)
            return False
        root, ext = os.path.splitext(module.__file__)
        if not ext in ('.py', '.pyc', '.pyo'):
            log.debug("no coverage of %s: not a python file", name)
            return False
        if tolist(self.options.cover_packages):
            for package in self.options.cover_packages:
                if (name.startswith(package)
                    and (self.options.cover_tests
                         or not self.conf.testMatch.search(name))):
                    log.debug("coverage for %s", name)
                    return True
        if name in self.skipModules:
            log.debug("no coverage for %s: loaded before coverage start",
                      name)
            return False
        if self.conf.testMatch.search(name) and not self.options.cover_tests:
            log.debug("no coverage for %s: is a test", name)
            return False
        # accept any package that passed the previous tests, unless
        # coverPackages is on -- in that case, if we wanted this
        # module, we would have already returned True
        return not self.options.cover_packages

    def wantFile(self, file, package=None):
        """If inclusive coverage enabled, return true for all source files
        in wanted packages."""
        if self.options.cover_inclusive:
            if file.endswith(".py"):
                if package and self.options.cover_packages:
                    for want in self.options.cover_packages:
                        if package.startswith(want):
                            return True
                else:
                    return True
        return None

