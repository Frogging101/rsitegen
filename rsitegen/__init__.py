import argparse
import logging
import os
import os.path as osp
import posixpath
import shutil
import stat
import sys

import jinja2

import rsitegen.conf
from rsitegen.conf import config
#import rsitegen.plugins
from rsitegen.node import *
import rsitegen.templates as templates
import rsitegen.util

logger = logging.getLogger()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="rsitegen: Static site generator")

    parser.add_argument("src", nargs='?', help="Source directory (SOURCEDIR)")
    parser.add_argument("dest", nargs='?', help="Output directory (DESTDIR)")
    parser.add_argument("-c", "--config", help="Configuration file to use")
    parser.add_argument('-D', "--debug", action="store_true", default=False,
                        help="Debug mode")

    args = parser.parse_args()

    assert args.debug is not None
    config["DEBUG"] = args.debug
    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.src is not None:
        config["SOURCEDIR"] = args.src

    if args.dest is not None:
        config["DESTDIR"] = args.dest

    return args


def init_config():
    required = ("SOURCEDIR", "DESTDIR")
    args = parse_arguments()
    if args.config is not None:
        config_file = args.config
    else:
        config_file = "siteconf.py"

    config.load_config_file(config_file)

    for req in required:
        if req not in config:
            logger.critical(req + " must be provided in the configuration file"
                                  " or on the command line.")
            sys.exit(1)


def init_logger():
    logger.addHandler(logging.StreamHandler())


def get_dir_template(dirpath, filenames):
    for template in config["DIRINDEX_TEMPLATES"]:
        if template in filenames:
            return osp.join(dirpath, template)

    return util.get_theme_template("directory")


def render_all(root, path='/'):
    cur = root
    logger.debug("Rendering directory %s (%s)", path, type(root).__name__)
    root.render(root, path)
    for name,child in root.children.items():
        childpath = posixpath.join(path, name)
        if isinstance(child, DirNode):
            render_all(child, childpath)
        else:
            logger.debug("Rendering %s (%s)", childpath,
                         type(child).__name__)
            child.render(root, childpath)


def main():
    init_logger()
    init_config()
    for k,v in config.items():
        logger.debug('config["' + k + '"]=' + str(v))

    jinja_env = templates.init_env()

    parent = None
    root = None
    for dirpath,dirnames,filenames in os.walk(config["SOURCEDIR"]):
        #logger.debug("Processing directory %s", dirpath)
        rel_dirpath = osp.relpath(dirpath, config["SOURCEDIR"])
        if rel_dirpath == '.':
            rel_dirpath = ''
        curdir = DirNode(rel_dirpath, parent, osp.basename(rel_dirpath), jinja_env,
                         get_dir_template(dirpath, filenames))
        if root is None:
            root = curdir
        parent = curdir

        for f in filenames:
            path = osp.join(dirpath, f)
            relpath = osp.join(rel_dirpath, f)
            #logger.debug("Processing file %s", path)
            # if osp.islink(path):
            #     node = LinkNode(relpath, os.readlink(path))
            #     continue

            splitext = osp.splitext(f)
            base = splitext[0]
            ext = splitext[1].lstrip('.')
            if ext in config["PAGE_EXTENSIONS"]:
                node = PageNode(relpath, jinja_env)
                name = base + ".html"
            elif ext in config["TEMPLATE_EXTENSIONS"]:
                node = TemplateNode(relpath, jinja_env, path)
                name = base
            else:
                node = FileCopyNode(relpath)
                name = f

            curdir.add_child(name, node)

    render_all(root)

    assets_src = osp.join(config["THEME"], "assets")
    assets_dest = osp.join(config["DESTDIR"],
                           config["THEME_ASSETS_PATH"].lstrip(osp.sep))

    if os.path.isdir(assets_src):
        copied = False
        while not copied:
            try:
                shutil.copytree(assets_src, assets_dest)
                copied = True
            except FileExistsError:
                if not stat.S_ISDIR(os.lstat(assets_dest).st_mode):
                    os.unlink(assets_dest)
                else:
                    shutil.rmtree(assets_dest)
