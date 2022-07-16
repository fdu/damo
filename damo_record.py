#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

"""
Record data access patterns of the target process.
"""

import argparse
import os
import signal
import subprocess
import time

import _damon
import _damon_dbgfs
import _damon_result
import _damo_paddr_layout

class DataForCleanup:
    target_is_ongoing = False
    orig_attrs = None
    rfile_path = None
    rfile_format = None
    rfile_permission = None
    remove_perf_data = False
    perf_pipe = None

data_for_cleanup = DataForCleanup()

def cleanup_exit(exit_code):
    if data_for_cleanup.perf_pipe:
        # End the perf
        data_for_cleanup.perf_pipe.send_signal(signal.SIGINT)
        data_for_cleanup.perf_pipe.wait()

        # Get perf script mid result
        rfile_mid_format = 'perf_script'
        perf_data = data_for_cleanup.rfile_path + '.perf.data'
        subprocess.call('perf script -i \'%s\' > \'%s\'' %
                (perf_data, data_for_cleanup.rfile_path),
                shell=True, executable='/bin/bash')

        if data_for_cleanup.remove_perf_data:
            os.remove(perf_data)
    else:
        rfile_mid_format = 'record'

    if not data_for_cleanup.target_is_ongoing:
        if _damon.is_damon_running():
            if _damon.turn_damon('off'):
                print('failed to turn damon off!')
            while _damon.is_damon_running():
                time.sleep(1)
        if data_for_cleanup.orig_attrs:
            if _damon.damon_interface() != 'debugfs':
                print('damo_record/cleanup_exit: ' +
                        'BUG: none-debugfs is in use but orig_attrs is not None')
            _damon_dbgfs.apply_debugfs_inputs(data_for_cleanup.orig_attrs)

    if (data_for_cleanup.rfile_format != None and
            rfile_mid_format != data_for_cleanup.rfile_format):
        rfile_path_mid = data_for_cleanup.rfile_path + '.mid'
        os.rename(data_for_cleanup.rfile_path, rfile_path_mid)
        result = _damon_result.parse_damon_result(rfile_path_mid,
                rfile_mid_format)
        _damon_result.write_damon_result(result, data_for_cleanup.rfile_path,
                data_for_cleanup.rfile_format,
                data_for_cleanup.rfile_permission)
        os.remove(rfile_path_mid)

    os.chmod(data_for_cleanup.rfile_path, data_for_cleanup.rfile_permission)

    exit(exit_code)

def sighandler(signum, frame):
    print('\nsignal %s received' % signum)
    cleanup_exit(signum)

def set_argparser(parser):
    _damon.set_implicit_target_monitoring_argparser(parser)
    parser.add_argument('-l', '--rbuf', metavar='<len>', type=int,
            help='length of record result buffer')
    parser.add_argument('-o', '--out', metavar='<file path>', type=str,
            default='damon.data', help='output file path')
    parser.add_argument('--output_type', choices=['record', 'perf_script'],
            default=None, help='output file\'s type')
    parser.add_argument('--leave_perf_data', action='store_true',
            default=False, help='don\'t remove the perf.data file')
    parser.add_argument('--output_permission', type=str, default='600',
            help='permission of the output file')

def main(args=None):
    global data_for_cleanup

    if not args:
        parser = argparse.ArgumentParser()
        set_argparser(parser)
        args = parser.parse_args()

    _damon.ensure_root_permission()
    data_for_cleanup.target_is_ongoing = args.target == 'ongoing'
    if data_for_cleanup.target_is_ongoing:
        skip_dirs_population = True
    else:
        skip_dirs_population = False
    err = _damon.initialize(args, skip_dirs_population)
    if err != None:
        print(err)
        exit(1)

    damon_record_supported = _damon.feature_supported('record')

    if not damon_record_supported:
        try:
            subprocess.check_output(['which', 'perf'])
        except:
            print('perf is not installed')
            exit(1)

        if args.rbuf:
            print('# \'--rbuf\' will be ignored')
    if not args.rbuf:
        args.rbuf = 1024 * 1024

    data_for_cleanup.rfile_format = args.output_type
    data_for_cleanup.remove_perf_data = not args.leave_perf_data
    data_for_cleanup.rfile_permission = int(args.output_permission, 8)
    if (data_for_cleanup.rfile_permission < 0o0 or
            data_for_cleanup.rfile_permission > 0o777):
        print('wrong --output_permission (%s)' %
                data_for_cleanup.rfile_permission)
        exit(1)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    if _damon.damon_interface() == 'debugfs':
        data_for_cleanup.orig_attrs = _damon_dbgfs.current_debugfs_inputs()
    else:
        data_for_cleanup.orig_attrs = None

    if not data_for_cleanup.target_is_ongoing:
        _damon.set_implicit_target_args_explicit(args)
        ctx = _damon.damon_ctx_from_damon_args(args)
        if damon_record_supported:
            ctx.set_record(args.rbuf, args.out)
        kdamonds = [_damon.Kdamond('0', [ctx])]
        _damon.apply_kdamonds(kdamonds)

    data_for_cleanup.rfile_path = args.out
    if os.path.isfile(data_for_cleanup.rfile_path):
        os.rename(data_for_cleanup.rfile_path,
                data_for_cleanup.rfile_path + '.old')

    if not data_for_cleanup.target_is_ongoing:
        if _damon.turn_damon('on'):
            print('could not turn DAMON on')
            cleanup_exit(-2)

        while not _damon.is_damon_running():
            time.sleep(1)

    if not damon_record_supported:
        data_for_cleanup.perf_pipe = subprocess.Popen(['perf', 'record', '-a',
            '-e', 'damon:damon_aggregated', '-o',
            data_for_cleanup.rfile_path + '.perf.data'])
    print('Press Ctrl+C to stop')

    if args.self_started_target == True:
        os.waitpid(ctx.targets[0].pid, 0)
    while _damon.is_damon_running():
        time.sleep(1)

    cleanup_exit(0)

if __name__ == '__main__':
    main()
