import functools

def memoize_when_activated(fun):
    @functools.wraps(fun)
    def wrapper(self):
        try:
            # case 1: we previously entered
            ret = self._cache[fun]
        except AttributeError:
            # case 2: we never entered
            return fun(self)
        except KeyError:
            # case 3: we entered but there's no cache
            # for this entry yet
            ret = self._cache[fun] = fun(self)
        return ret

    def cache_activate(proc):
        proc._cache = {}

    def cache_deactivate(proc):
        try:
            del proc._cache            
        except AttributeError:
            pass

    wrapper.cache_activate = cache_activate
    wrapper.cache_deactivate = cache_deactivate
    return wrapper
