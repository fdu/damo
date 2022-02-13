#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

"""
Contains core functions for DAMON sysfs control.
"""

import os

import _damon

feature_supports = None

kdamonds_dir = '/sys/kernel/mm/damon/admin/kdamonds'

class DamonSysfsFile:
    indices = None  # e.g., {'kdamond': 0, 'context': 1}
    extra_path = None

    def __init__(self, indices, extra_path=None):
        self.indices = indices
        self.extra_path = extra_path

    def path(self):
        path = kdamonds_dir
        for keyword in ['kdamond', 'context', 'scheme', 'target',
                'region']:
            if keyword in self.indices:
                path = os.path.join(path, keyword + 's', self.indices[keyword])
        if self.extra_path:
            path = os.path.join(path, self.extra_path)
        return path

    def __str__(self):
        return self.path()

    def __repr__(self):
        return self.path()

    def regions_dir(self):
        return DamonSysfsFile(file_idx='regions',
                kdamond_idx=self.kdamond_idx, context_idx=self.context_idx,
                target_idx=self.target_idx)

    def regions_nr(self):
        return DamonSysfsFile(file_idx='regions/nr',
                kdamond_idx=self.kdamond_idx, context_idx=self.context_idx,
                target_idx=self.target_idx)

    def write(self, content):
        with open(self.path(), 'w') as f:
            f.write(content)

def _write(content, filepath):
    with open(filepath, 'w') as f:
        f.write(content)

def _ensure_sysfs_dir_for_damo():
    if not os.isdir(sysfs_damon + 'kdamonds/0')):
        _write('1', sysfs_damon + 'kdamonds/nr')
    if not os.isdir(sysfs_damon + 'kdamonds/0/contexts/0'):
        _write('1', sysfs_damon + 'kdamonds/0/contexts/nr')

def set_target(tid, init_regions):
    _ensure_sysfs_dir_for_damo()
    if not os.isdir(sysfs_damon + 'kdamonds/0/contexts/0/targets/0'):
        _write('1', sysfs_damon + 'kdamonds/0/contexts/0/targets/nr')
    if tid == 'paddr':
        _write('paddr\n', sysfs_damon + 'kdamonds/0/contexts/0/damon_type')
    else:
        _write('%s\n' % tid, sysfs_damon +
                'kdamonds/0/contexts/0/targets/0/pid')

    _write('%s' % len(init_regions), sysfs_damon +
            'kdamonds/0/contexts/0/targets/0/regions/nr')
    for idx, region in enumerate(init_regions):
        _write(region[0], sysfs_damon +
                'kdamonds/0/contexts/0/targets/0/regions/%d/start')
        _write(region[1], sysfs_damon +
                'kdamonds/0/contexts/0/targets/0/regions/%d/end')

def turn_damon(on_off):
    pass

def is_damon_running():
    pass

def attrs_apply(attrs):
    pass

def current_attrs():
    pass

def feature_supported(feature):
    if feature_supports == None:
        chk_update()
    return feature_supports[feature]

def get_supported_features():
    if feature_supports == None:
        chk_update()
    return feature_supports

def chk_update():
    if not os.path.isdir(sysfs_damon):
        print('damon sysfs dir (%s) not found' % sysfs_damon)
        exit(1)

    feature_supports = {x: True for x in _damon.features}

def cmd_args_to_attrs(args):
    pass

def cmd_args_to_init_regions(args):
    pass

def set_attrs_argparser(parser):
    pass

def set_init_regions_argparser(parser):
    pass
