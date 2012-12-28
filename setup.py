#!/usr/bin/env python
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

from setuptools import setup, find_packages

setup(
    name='BittenExtraNose',
    version='0.2',
    author='Pedro Algarvio',
    author_email = 'ufs@ufsoft.org',
    description = 'Bitten Nose plugins',
    license = 'BSD',
    packages = find_packages(),
    install_requires=['nose>=0.9.2', 'bitten==dev,>=0.6dev-r378'],
    entry_points = {
        'nose.plugins.0.10': [
            'bitten#nosetests = nosebitten.plugnose:BittenNosetests',
            'bitten#nosecoverage = nosebitten.plugnose:BittenNoseCoverage'
        ]
    }
)
