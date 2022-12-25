#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import argparse

class DamoSubCmdModule:
    set_argparser = None
    main = None

    def __init__(self, set_argparser, main):
        self.set_argparser = set_argparser
        self.main = main

class DamoSubCmd:
    name = None
    msg = None
    module = None

    def __init__(self, name, module, msg):
        self.name = name
        self.module = module
        self.msg = msg

    def add_parser(self, subparsers):
        subparser = subparsers.add_parser(self.name, help=self.msg)
        self.module.set_argparser(subparser)

    def execute(self, args):
        self.module.main(args)