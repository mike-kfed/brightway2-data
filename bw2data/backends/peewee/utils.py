# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ... import Method


def dict_as_activitydataset(ds):
    return {
        "data": ds,
        "database": ds["database"],
        "key": (ds["database"], ds["code"]),
        "location": ds.get("location"),
        "name": ds.get("name"),
        "product": ds.get("reference product"),
        "type": ds.get("type", "process"),
    }


def dict_as_exchangedataset(ds):
    return {
        "data": ds,
        "input": ds['input'],
        "output": ds['output'],
        "database": ds['output'][0],
        "type": ds['type']
    }


def replace_exchanges(old_key, new_key):
    """Replace ``old_key`` with ``new_key`` in input field of exchanges.

    Returns number of modified exchanges."""
    from .proxies import Exchanges

    # reverse means search by input field, not output field of exchange
    for index, exc in enumerate(Exchanges(old_key, reverse=True)):
        exc["input"] = new_key
        exc.save()
    return index + 1


def replace_cfs(old_key, new_key):
    """Replace ``old_key`` with ``new_key`` in characterization factors.

    Returns list of modified methods."""
    for name in methods:
        changed, lst = False. []
        data = Method(name).load()
        for line in data:
            if line[0] == old_key:
                line[0] = new_key
                changed = True
        if changed:
            Method(name).write(data)
            lst.append(name)
        return lst
