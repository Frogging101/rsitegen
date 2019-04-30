import copy
from importlib.util import spec_from_file_location, module_from_spec
from importlib.machinery import SourceFileLoader
import logging
import os.path as osp

logger = logging.getLogger(__name__)

DEFAULT_THEME = osp.join(osp.abspath(osp.dirname(__file__)),
                         "themes", "default")

DEFCONFIG = {
    "DIRINDEX_TEMPLATES": ("index.html.template",),
    "DIRINDEX": "index.html",
    "PAGE_EXTENSIONS": ("md",),
    "TEMPLATE_EXTENSIONS": ("template",),
    "THEME": DEFAULT_THEME,
    "THEME_ASSETS_PATH": "/assets",
}

class Config:
    def __init__(self):
        self._config = copy.deepcopy(DEFCONFIG)

    def load_config_file(self, config_path):
        # Load the configuration script as a module and insert its
        # variables into the config dictionary
        loader = SourceFileLoader("siteconf", config_path)

        spec = spec_from_file_location("siteconf", config_path)
        module = module_from_spec(spec)

        try:
            loader.exec_module(module)
        except FileNotFoundError:
            return
        except OSError as e:
            logger.warning("Failed to open "+config_file+": " + e.strerror)
            return

        for k,v in module.__dict__.items():
            if (k.isupper()):
                self._config[k] = v


    def __getitem__(self, key):
        return self._config.__getitem__(key)

    def __setitem__(self, key, value):
        self._config.__setitem__(key, value)

    def __iter__(self):
        return self._config.__iter__()

    def __contains__(self, key):
        return self._config.__contains__(key)

    def keys(self):
        return self._config.keys()

    def values(self):
        return self._config.values()

    def items(self):
        return self._config.items()

config = Config()
