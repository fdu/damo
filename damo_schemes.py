#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

"""
Apply given operation schemes.
"""

import os
import signal

import _damon
import _damon_args

def cleanup_exit(exit_code):
    kdamonds_names_to_turn_off = []
    if kdamonds_names != None:
        for kdamond_name in kdamonds_names:
            if _damon.is_kdamond_running(kdamond_name):
                kdamonds_names_to_turn_off.append(kdamond_name)
    err = _damon.turn_damon_off(kdamonds_names_to_turn_off)
    if err:
        print('failed to turn damon off (%s)' % err)
    err = _damon.apply_kdamonds(orig_kdamonds)
    if err:
        print('failed restoring previous kdamonds setup (%s)' % err)
    exit(exit_code)

def sighandler(signum, frame):
    print('\nsignal %s received' % signum)
    cleanup_exit(signum)

def set_argparser(parser):
    return _damon_args.set_argparser(parser, add_record_options=False)

def main(args=None):
    global orig_kdamonds
    global kdamonds_names

    if not args:
        parser = set_argparser(None)
        args = parser.parse_args()

    _damon.ensure_root_and_initialized(args)

    orig_kdamonds = _damon.current_kdamonds()
    kdamonds_names = None

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    err, kdamonds = _damon_args.turn_damon_on(args)
    if err:
        print('could not turn DAMON on (%s)' % err)
        cleanup_exit(-3)

    kdamonds_names = [k.name for k in kdamonds]

    print('Press Ctrl+C to stop')
    if _damon_args.self_started_target(args):
        os.waitpid(kdamonds[0].contexts[0].targets[0].pid, 0)
    # damon will turn it off by itself if the target tasks are terminated.
    _damon.wait_current_kdamonds_turned_off()

    cleanup_exit(0)

if __name__ == '__main__':
    main()
