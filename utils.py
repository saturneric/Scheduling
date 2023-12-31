import json


def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls


def auto_repr(cls):
    def __repr__(self):
        return str(self.__dict__)

    cls.__repr__ = __repr__
    return cls


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=4, sort_keys=False)
