# -*- coding: utf-8 -*-
from __future__ import print_function
from . import Database, databases, Method, methods, config, Weighting, \
    weightings, Normalization, normalizations
from .ia_data_store import abbreviate
from .utils import recursive_str_to_unicode
import os
import pprint
try:
    import progressbar
except ImportError:
    progressbar = None
import re
import warnings

try:
    import cPickle as pickle
except ImportError:
    import pickle

hash_re = re.compile("^[a-zA-Z0-9]{32}$")
is_hash = lambda x: bool(hash_re.match(x))

UPTODATE_WARNING = "\n\nYour data needs to be updated. Please run the following program on the command line:\n\n\tbw2-uptodate\n"

if progressbar:
    widgets = [
        progressbar.SimpleProgress(sep="/"), " (",
        progressbar.Percentage(), ') ',
        progressbar.Bar(marker=progressbar.RotatingMarker()), ' ',
        progressbar.ETA()
    ]


class Updates(object):
    UPDATES = {
        "1.0 reprocess all objects": {
            'method': "reprocess_all_1_0",
            'explanation': "1.0 relaxed previous restrictions on what had to be included in Databases, IA methods, etc. These objects need to be reprocessed to put in default values."},
    }

    @staticmethod
    def explain(key):
        return Updates.UPDATES[key]['explanation']

    @staticmethod
    def do_update(key):
        method = getattr(Updates, Updates.UPDATES[key]['method'])
        method()
        config.p['updates'][key] = True
        config.save_preferences()

    @staticmethod
    def check_status(verbose=True):
        """Check if updates need to be applied.

        Returns:
            List of needed updates (strings), if any.

        """
        updates = []

        if "updates" not in config.p:
            config.p['updates'] = {key: True for key in Updates.UPDATES}
            config.save_preferences()
        else:
            updates = sorted([key for key in Updates.UPDATES if not config.p['updates'].get(key)])
        if updates and verbose:
            warnings.warn(UPTODATE_WARNING)
        return updates

    @staticmethod
    def reprocess_all_1_0():
        """1.0: Reprocess all to make sure default 'loc' value inserted when not specified."""
        objects = [
            (methods, Method, "LCIA methods"),
            (weightings, Weighting, "LCIA weightings"),
            (normalizations, Normalization, "LCIA normalizations"),
            (databases, Database, "LCI databases"),
        ]

        for (meta, klass, name) in objects:
            if meta.list:
                print("Updating all %s" % name)

                if progressbar:
                    pbar = progressbar.ProgressBar(
                        widgets=widgets,
                        maxval=len(meta)
                    ).start()

                for index, key in enumerate(meta):
                    obj = klass(key)
                    obj.process()
                    # Free memory
                    obj = None

                    if progressbar:
                        pbar.update(index)

                if progressbar:
                    pbar.finish()
