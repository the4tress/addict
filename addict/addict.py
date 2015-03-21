from inspect import isgenerator
import re

class Dict(dict):
    """
    Dict is a subclass of dict, which allows you to get AND SET(!!)
    items in the dict using the attribute syntax!

    When you previously had to write:

    my_dict = {'a': {'b': {'c': [1, 2, 3]}}}

    you can now do the same simply by:

    my_Dict = Dict()
    my_Dict.a.b.c = [1, 2, 3]

    Or for instance, if you'd like to add some additional stuff,
    where you'd with the normal dict would write

    my_dict['a']['b']['d'] = [4, 5, 6],

    you may now do the AWESOME

    my_Dict.a.b.d = [4, 5, 6]

    instead. But hey, you can always use the same syntax as a regular dict,
    however, this will not raise TypeErrors or AttributeErrors at any time
    while you try to get an item. A lot like a defaultdict.

    """
    def __init__(self, *args, **kwargs):
        """
        If we're initialized with a dict, make sure we turn all the
        subdicts into Dicts as well.

        """
        for arg in args:
            if not arg:
                continue
            elif isinstance(arg, dict):
                for key, val in arg.items():
                    self[key] = val
            elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
                self[arg[0]] = arg[1]
            elif isinstance(arg, (list, tuple)) or isgenerator(arg):
                for key, val in arg:
                    self[key] = val
            else:
                raise TypeError("Dict does not understand "
                                "{0} types".format(type(arg)))

        for key, val in kwargs.items():
            self[key] = val

    def __setattr__(self, name, value):
        """
        setattr is called when the syntax a.b = 2 is used to set a value.

        """
        if hasattr(Dict, name):
            raise AttributeError("'Dict' object attribute "
                                 "'{0}' is read-only".format(name))
        else:
            self[name] = value

    def __setitem__(self, name, value):
        """
        This is called when trying to set a value of the Dict using [].
        E.g. some_instance_of_Dict['b'] = val. If 'val

        """
        value = self._hook(value)
        super(Dict, self).__setitem__(name, value)

    @classmethod
    def _hook(cls, item):
        """
        Called to ensure that each dict-instance that are being set
        is a addict Dict. Recurses.

        """
        if isinstance(item, dict):
            return cls(item)
        elif isinstance(item, (list, tuple)):
            return type(item)(cls._hook(elem) for elem in item)
        return item

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, name):
        """
        This is called when the Dict is accessed by []. E.g.
        some_instance_of_Dict['a'];
        If the name is in the dict, we return it. Otherwise we set both
        the attr and item to a new instance of Dict.

        """
        if name not in self:
            self[name] = {}
        return super(Dict, self).__getitem__(name)

    def __delattr__(self, name):
        """
        Is invoked when del some_instance_of_Dict.b is called.

        """
        del self[name]

    _re_pattern = re.compile('[a-zA-Z_][a-zA-Z0-9_]*')

    def __dir__(self):
        """
        Return a list of addict object attributes.
        This includes key names of any dict entries, filtered to the subset of
        valid attribute names (e.g. alphanumeric strings beginning with a letter
        or underscore).  Also includes attributes of parent dict class.
        """
        dict_keys = []
        for k in self.keys():
            if isinstance(k, str):
                m = self._re_pattern.match(k)
                if m:
                    dict_keys.append(m.string)

        obj_attrs = list(dir(Dict))

        return dict_keys + obj_attrs

    def _ipython_display_(self):
        print(str(self))    # pragma: no cover

    def _repr_html_(self):
        return str(self)

    def prune(self, prune_zero=False, prune_empty_list=True):
        """
        Removes all empty Dicts and falsy stuff inside the Dict.
        E.g
        >>> a = Dict()
        >>> a.b.c.d
        {}
        >>> a.a = 2
        >>> a
        {'a': 2, 'b': {'c': {'d': {}}}}
        >>> a.prune()
        >>> a
        {'a': 2}

        Set prune_zero=True to remove 0 values
        E.g
        >>> a = Dict()
        >>> a.b.c.d = 0
        >>> a.prune(prune_zero=True)
        >>> a
        {}

        Set prune_empty_list=False to have them persist
        E.g
        >>> a = Dict({'a': []})
        >>> a.prune()
        >>> a
        {}
        >>> a = Dict({'a': []})
        >>> a.prune(prune_empty_list=False)
        >>> a
        {'a': []}
        """
        for key, val in list(self.items()):
            if ((not val) and ((val != 0) or prune_zero) and
                    not isinstance(val, list)):
                del self[key]
            elif isinstance(val, Dict):
                val.prune(prune_zero, prune_empty_list)
                if not val:
                    del self[key]
            elif isinstance(val, (list, tuple)):
                new_iter = self._prune_iter(val, prune_zero, prune_empty_list)
                if (not new_iter) and prune_empty_list:
                    del self[key]
                else:
                    if isinstance(val, tuple):
                        new_iter = tuple(new_iter)
                    self[key] = new_iter

    @classmethod
    def _prune_iter(cls, some_iter, prune_zero=False, prune_empty_list=True):

        new_iter = []
        for item in some_iter:
            if item == 0 and prune_zero:
                continue
            elif isinstance(item, Dict):
                item.prune(prune_zero, prune_empty_list)
                if item:
                    new_iter.append(item)
            elif isinstance(item, (list, tuple)):
                new_item = type(item)(
                    cls._prune_iter(item, prune_zero, prune_empty_list))
                if new_item or not prune_empty_list:
                    new_iter.append(new_item)
            else:
                new_iter.append(item)
        return new_iter

    def to_dict(self):
       """
       Recursively turn your addict Dicts into dicts.

       """
       base = {}
       for key, value in self.items():
           if isinstance(value, type(self)):
               base[key] = value.to_dict()
           elif isinstance(value, (list, tuple)):
               base[key] = type(value)(
                item.to_dict() if isinstance(item, type(self)) else
                item for item in value)
           else:
               base[key] = value
       return base

    def copy(self):
        """
        Return a disconnected deep copy of self. Children of type Dict, list
        and tuple are copied recursively while values that are instances of
        other mutable objects are not copied.

        """
        return Dict(self.to_dict())

    def update(self, d):
        """
        Recursively merge d into self.

        """
        for k, v in d.items():
            if (k not in self) or (not isinstance(self[k], dict)) or (not isinstance(v, dict)):
                self[k] = v
            else:
                self[k].update(v)

    def extend(self, *args, **kwargs):
        '''
            Python version of jQuery's $.extend().

            Merges the contents of two or more dicts together into the first dict.

            kwarg options:
                deep            True/False
                list_action    ['replace', 'append', 'ammend']
                    default is 'replace'

            NOTE: I can't figure out how to update an object. As you can see in
                the examples I always say e = e.extend() instead of just e.extend()

            Examples:
                defaults = Dict()
                defaults.tier_1_1.teir_2_0 = False
                defaults.tier_1_1.teir_2_1 = 1
                defaults.tier_1_1.teir_2_2 = 'a string'
                defaults.tier_1_1.teir_2_3 = ['this', 'is', 'DEEP']
                defaults.tier_1_2 = ['a', 'b', 'c']
                # Dictionary verison
                # defaults = {
                #     'tier_1_1': {
                #         'tier_2_0': False,
                #         'tier_2_1': 1,
                #         'tier_2_2': 'a string',
                #         'tier_2_3': ['this', 'is', 'DEEP']
                #     },
                #     'tier_1_2': ['a', 'b', 'c']
                # }

                params = Dict()
                params.tier_1_0 = 'another string'
                params.tier_1_1.tier_2_0 = True
                params.tier_1_1.tier_2_1 = 234234
                params.tier_1_1.tier_2_4.tier_3_0 = 'really deep dict'
                params.tier_1_2 = ['d', 'e']
                # Dictionary verison
                # params = {
                #     'tier_1_0': 'another string',
                #     'tier_1_1': {
                #         'tier_2_0': True,
                #         'tier_2_1': 234234,
                #         'tier_2_4': {
                #             'tier_3_0': 'really deep dict'
                #         }
                #     },
                #     'tier_1_2': ['d', 'e']
                # }

                e = Dict()
                # Extend just the first tier. I think this is pretty much the same
                #   as your update(), except I also have the list actions (which
                #   may or may not be valuable.)
                e = e.extend(defaults, params)
                OUTPUT
                    {
                        "tier_1_1": {
                            "tier_2_1-int": 234234,
                            "tier_2_0-bool": true,
                            "tier_2_4-dict": {
                                "tier_3_0": "deep dict"
                            }
                        },
                        "tier_1_0": "another string",
                        "tier_1_2": ["d", "e"]
                    }

                # Extend deep and append any intersecting lists
                e = e.extend(defaults, params, deep=True, list_action="append")
                OUTPUT
                    {
                        "tier_1_1": {
                            "tier_2_2-str": "a string",
                            "tier_2_1-int": 234234,
                            "tier_2_0-bool": true,
                            "tier_2_4-dict": {
                                "tier_3_0": "deep dict"
                            },
                            "tier_2_3-list": ["this", "is", "DEEP"]
                        },
                        "tier_1_0": "another string",
                        "tier_1_2": ["a", "b", "c", "d", "e"]
                    }

                # Extend deep and ammend any intersecting lists
                e = e.extend(defaults, params, deep=True, list_action="ammend")
                OUTPUT
                {
                    "tier_1_1": {
                        "tier_2_2-str": "a string",
                        "tier_2_1-int": 234234,
                        "tier_2_0-bool": true,
                        "tier_2_4-dict": {
                            "tier_3_0": "deep dict"
                        },
                        "tier_2_3-list": ["this", "is", "DEEP"]
                    },
                    "tier_1_0": "another string",
                    "tier_1_2": ["d", "e", "c"]
                }
        '''

        # Error checking for kwargs
        # deep must be True or False if it is defined
        if 'deep' in kwargs and type(kwargs['deep']) != bool:
            raise TypeError("'deep' expects a boolean.")
        if 'list_action' in kwargs and kwargs['list_action'] not in ['replace', 'append', 'ammend']:
            raise ValueError("'list_action' must be one of the following: 'replace', 'append', 'ammend'")

        # Define defaults for optional params
        deep = kwargs['deep'] if 'deep' in kwargs else False
        list_action = 'replace' if 'list_action' not in kwargs else kwargs['list_action']
        first_iter = False if 'first_iter' in kwargs else True

        # For each arg in args, convert arg to dict if arg is Dict()
        [ arg.to_dict() if isinstance(arg, type(self)) else arg for arg in args ]

        extended = None

        for arg in args:
            # Reset extended if the types don't match.
            # This prevents extending a dict over a list.
            extended = None if extended != None and type(extended) != type(arg) else extended

            if isinstance(arg, Dict):
                arg.to_dict()

            if isinstance(arg, dict):
                if extended == None:
                    extended = {}

                for item in arg:
                    if deep:
                        # Recursion
                        kwargs['first_iter'] = False
                        extended[item] = arg[item] if item not in extended else self.extend(extended[item], arg[item], **kwargs)
                    else:
                        extended[item] = arg[item]

            elif isinstance(arg, (list, tuple)):
                is_tuple = False
                # If its a tuple, convert it to a list
                if type(arg) == tuple:
                    arg = [a for a in arg]
                    is_tuple = True

                if extended == None:
                    extended = []

                if list_action == 'append':
                    for item in arg:
                        extended.append(item)

                elif list_action == 'ammend':
                    for idx, item in enumerate(arg):
                        if deep:
                            # Recursion
                            kwargs['first_iter'] = False
                            extended = self.extend([a for a in arg] + [e for e in extended[len(arg) - len(extended):]], **kwargs) if len(extended) > len(arg) else arg
                        else:
                            extended = [a for a in arg] + [e for e in extended[len(arg) - len(extended):]] if len(extended) > len(arg) else arg
                else:
                    extended = arg

                # If it started out as a tuple, convert it back to tuple
                if is_tuple:
                    arg = tuple(a for a in arg)

            # str, int, float, long, complex, bool, etc...
            else:
                extended = arg

        return Dict(extended) if first_iter is True else extended

