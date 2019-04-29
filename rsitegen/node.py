from functools import total_ordering
import logging
from math import floor
import os
import posixpath
import os.path as osp
import shutil
import time

from rsitegen.conf import config
from rsitegen.parser import parse_markdown
import rsitegen.util as util

logger = logging.getLogger()

class NodeError(Exception):
    pass

class NotADirectoryNodeError(NodeError):
    pass

#@total_ordering
class Node:
    def __init__(self, src):
        self._src = src

        if not hasattr(self, "_ts"):
            t = time.time()
            sec = floor(t)
            nsec = (t - sec) * 10**9
            self._ts = (sec, nsec)


    @property
    def src(self):
        return self._src


#@total_ordering
class LinkNode(Node):
    def __init__(self, src, target, **kwargs):
        self._target = target
        super().__init__(src, **kwargs)


    @property
    def target(self):
        return self._target


    def render(self, root, path):
        pass

class FileCopyNode(Node):
    def __init__(self, src, **kwargs):
        self._ts = util.filetime(osp.join(config["SOURCEDIR"], src))
        super().__init__(src, **kwargs)


    def render(self, root, path):
        copyfrom = osp.join(config["SOURCEDIR"], self._src)
        copyto = osp.join(config["DESTDIR"], util.p2os(path.lstrip('/')))
        logger.info("Copying: %s → %s", copyfrom, copyto)
        os.makedirs(osp.dirname(copyto), exist_ok=True)
        shutil.copy2(copyfrom, copyto)


class FileNode(Node):
    def __init__(self, src, data, **kwargs):
        self._data = data
        super().__init__(src, **kwargs)


    def render(self, root, path):
        destfile = osp.join(config["DESTDIR"], util.p2os(path.lstrip('/')))
        os.makedirs(osp.dirname(destfile), exist_ok=True)
        with open(destfile, 'w') as f:
            f.write(self._data)


class DirContext():
    def __init__(self, root, path):
        self.root = root
        self.path = path


class TemplateNode(Node):
    def __init__(self, src, env, template, context=None, **kwargs):
        self._env = env
        self._template = template
        if context is None:
            context = dict()
        self._context = context
        super().__init__(src, **kwargs)


    @property
    def template(self):
        return self._template


    def render(self, root, path):
        template = self._env.get_template(self._template)
        self._context["dir_context"] = DirContext(root, path)
        self._context["node"] = self
        output = template.render(self._context)
        destfile = osp.join(config["DESTDIR"], util.p2os(path.lstrip('/')))
        with open(destfile, 'w') as f:
            f.write(output)


class DirNode(TemplateNode):
    def __init__(self, src, parent, name, env, template, **kwargs):
        self._parent = parent
        if parent:
             parent.add_child(name, self)
        logger.debug("Creating directory node %s (parent 0x%x, name %s)",
                     self, id(parent), name)
        self._children = dict()
        super().__init__(src, env, template, **kwargs)


    @property
    def children(self):
        return dict(self._children)

    @property
    def parent(self):
        return self._parent


    def root(self):
        cur = self
        while cur.parent:
            cur = cur.parent

        return cur

    def step_path(self, path, stop_at_none=False):
        if isinstance(path, list):
            posixpath.join(path)
        if util.is_dirpath(path):
            path = path.rstrip('/')
        dirname = posixpath.dirname(path)
        basename = posixpath.basename(path)

        cur = self
        for elem in util.split_path(dirname):
            if cur is None:
                if stop_at_none:
                    return
                yield None
                continue

            if elem == '/':
                cur = self.root()
            elif elem == '.':
                continue
            elif elem == "..":
                if cur.parent is None:
                    continue
                cur = cur.parent
            else:
                child = cur._children.get(elem)
                if isinstance(child, DirNode):
                    cur = child
                elif child is None:
                    cur = None
                else:
                    raise NotADirectoryNodeError

            yield cur

        if cur is not None:
            yield cur._children.get(basename)
        else:
            yield None

    def lookup_path(self, path):
        node = None
        for node in self.step_path(path, True):
            pass

        return node

    def add_child(self, name, node):
        assert isinstance(node, Node)
        self._children[name] = node

    def rm_child(self, name):
        try:
            del self._children[name]
        except KeyError:
            pass

    def mv(self, source, target, makedirs=False):
        # `target` is handled as follows:
        # - If it ends with a slash, the node will be added to the
        #   directory before the slash, with the name set to the source's
        #   basename.
        # - Otherwise, the node will be moved to the directory at the
        #   target's dirname, with the name set to the target's basename.

        if util.is_root(source):
            raise ValueError
        source = source.rstrip('/')
        source_dir = self.lookup_path(posixpath.dirname(source))
        if source_dir is None:
            raise KeyError

        target_is_dirpath = util.is_dirpath(target)
        target_dir = None
        prev = None
        if target_is_dirpath:
            elems = util.split_path(target.rstrip('/'))
        else:
            elems = util.split_path(target)
        i = 0
        for target_node in self.step_path(elems):
            if target_node is None:
                if i == len(elems)-1 and not target_is_dirpath:
                    break

                if not makedirs:
                    raise KeyError
                target_node = DirNode(None, prev, elems[i], self._env,
                                      util.get_theme_template("directory"))

            prev = target_node
            i += 1

        if target_is_dirpath:
            target_dir = target_node
            destname = posix.basename(source)
        else:
            target_dir = prev
            destname = posix.basename(target)

        srcname = posix.basename(source)
        source_node = source_dir.children[srcname]
        source_dir.rm_child(srcname)
        target_dir.add_child(destname, child)
        if isinstance(child, DirNode):
            child._parent = target_dir


    def render(self, root, path):
        os.makedirs(
            osp.join(config["DESTDIR"],
                     util.p2os(path.lstrip('/'))),
            exist_ok=True
        )
        super().render(root, posixpath.join(path, config["DIRINDEX"]))


class PageNode(TemplateNode):
    def __init__(self, src, env, **kwargs):
        template = util.get_theme_template("page")
        super().__init__(src, env, template, **kwargs)

    def render(self, root, path):
        self._context["page"] = parse_markdown(self._src)
        super().render(root, path)
