import os
import os.path as osp
import posixpath

import jinja2

import rsitegen.conf
from rsitegen.conf import config


def siteurl(path):
    return posixpath.join(config["SITEURL"], path.lstrip('/'))


def init_env():
    default_templates_dir = osp.join(rsitegen.conf.DEFAULT_THEME, "templates")
    theme_templates_dir = osp.join(config["THEME"], "templates")

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([theme_templates_dir,
                                        default_templates_dir,
                                        os.curdir]),
        autoescape=False
    )
    jinja_env.globals["config"] = config
    jinja_env.globals["siteurl"] = siteurl

    return jinja_env
