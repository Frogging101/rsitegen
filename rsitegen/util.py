import os
import os.path as osp
import posixpath

from rsitegen.conf import config

def get_theme_template(template):
    return template + ".template"


def filetime(path):
    stat = os.lstat(path)
    return (stat.st_mtime, stat.st_mtime_ns)


def get_path_module(os):
    if os:
        return osp
    return posixpath


def is_root(path, os=False):
    path_module = get_path_module(os)
    if not path.rstrip(path_module.sep):
        return True
    return False


def is_dirpath(path, os=False):
    path_module = get_path_module(os)
    stripped = path.rstrip(path_module.sep)
    # If stripped is empty, it is the root
    if stripped and stripped != path:
        return True
    return False


def split_path(path, os=False, keep_trailing=False):
    elements = list()
    if not path:
        return elements

    path_module = get_path_module(os)

    # Handle and remove trailing slashes before calling split()
    if keep_trailing and is_dirpath(path, os):
        elements.append('')
    if is_dirpath(path, os):
        path = path.rstrip(path_module.sep)

    split = path_module.split(path)
    while split[1]:
        elements.append(split[1])
        split = path_module.split(split[0])
    elements.append(split[0])

    elements.reverse()
    return elements


def os2p(path):
    if not path:
        return ''
    return posixpath.join(*split_path(path, os=True))


def p2os(path):
    if not path:
        return ''
    return osp.join(*split_path(path, os=False))
