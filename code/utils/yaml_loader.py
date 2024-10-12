import re
import os
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

_cache = {}

class YamlLoader(Loader):
    def __init__(self, stream):
        # register the tag handler
        self._stream = stream
        self.add_constructor('!concat', self._concat)
        self.add_constructor('!ref', self._ref)
        super(YamlLoader, self).__init__(stream)

    @staticmethod
    def _concat(loader, node):
        seq = loader.construct_sequence(node)
        return ''.join([str(i) for i in seq])

    def _ref(self, loader, node):
        seq = loader.construct_sequence(node)
        f = str(seq[0])
        field = str(seq[1])
        return self._get_field_from_file(loader, f, field)

    @staticmethod
    def _open_file(loader, f):

        stream_path = getattr(loader._stream, 'name', None)

        if not stream_path:
            dir_path = os.path.dirname(os.path.realpath(__file__))
        else:
            dir_path = os.path.dirname(os.path.realpath(stream_path))

        return open(dir_path + '/' + f, 'r')

    def _get_dic_from_file(self, loader, f):

        global _cache

        # use cache
        if f in _cache:
            return _cache[f]

        stream = YamlLoader._open_file(loader, f)
        dic = load(stream, Loader=YamlLoader)
        stream.close()

        # insert in cache
        _cache[f] = dic

        return dic

    def _get_field_from_file(self, loader, f, dotted_field):
        dic = self._get_dic_from_file(loader, f)
        ans = YamlLoader._get_inner_field(dic, dotted_field)
        return ans

    @staticmethod
    def _get_inner_field(dic, dotted_field):
        arr = dotted_field.split('.')
        ans = dic[arr[0]]

        if len(arr) == 1:
            return ans
        else:
            for x in arr[1:]:
                ans = ans[x]
            return ans

class LoaderIgnoreTags(Loader):
    def __init__(self,stream):
        self.add_constructor('!concat', self.ignore_tags)
        self.add_constructor('!ref', self.ignore_tags)
        self.fetch_alias = Loader.fetch_plain
        self.fetch_anchor = Loader.fetch_plain
        super(LoaderIgnoreTags, self).__init__(stream)

    def ignore_tags(self, node):
        return node.tag +  ' [' + ','.join([item.value for item in node.value]) + ']'