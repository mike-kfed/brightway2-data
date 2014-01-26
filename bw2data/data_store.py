# -*- coding: utf-8 -*
from .errors import UnknownObject
from . import config
import numpy as np
import os
import warnings
try:
    import cPickle as pickle
except ImportError:
    import pickle


class DataStore(object):
    validator = None
    metadata = None
    dtype_fields = None
    base_uncertainty_fields = [
        ('uncertainty_type', np.uint8),
        ('amount', np.float32),
        ('loc', np.float32),
        ('scale', np.float32),
        ('shape', np.float32),
        ('minimum', np.float32),
        ('maximum', np.float32),
        ('negative', np.bool),
    ]

    def __init__(self, name):
        self.name = name
        if self.name not in self.metadata and not \
                getattr(config, "dont_warn", False):
            warnings.warn(u"\n\t%s is not registered" % self, UserWarning)

    def __unicode__(self):
        return u"Brightway2 %s: %s" % (self.__class__.__name__, self.name)

    def __str__(self):
        return unicode(self).encode('utf-8')

    @property
    def filename(self):
        return self.name

    def register(self, **kwargs):
        """Register an object with the metadata store.

        Objects must be registered before data can be written. If this object is not yet registered in the metadata store, a warning is written to **stdout**.

        Takes any number of keyword arguments.

        """
        assert self.name not in self.metadata, u"%s is already registered" % self
        self.metadata[self.name] = kwargs

    def deregister(self):
        """Remove an object from the metadata store. Does not delete any files."""
        del self.metadata[self.name]

    def assert_registered(self):
        if self.name not in self.metadata:
            raise UnknownObject(u"%s is not yet registered" % self)

    def load(self):
        """Load the intermediate data for this object.

        Returns:
            The intermediate data.

        """
        self.assert_registered()
        try:
            return pickle.load(open(os.path.join(
                config.dir,
                u"intermediate",
                self.filename + u".pickle"
            ), "rb"))
        except OSError:
            raise MissingIntermediateData(u"Can't load intermediate data")

    @property
    def dtype(self):
        return self.dtype_fields + self.base_uncertainty_fields

    def copy(self, name):
        """Make a copy of this object. Takes new name as argument."""
        assert name not in self.metadata, u"%s already exists" % name
        new_obj = self.__class__(name)
        new_obj.register(**self.metadata[self.name])
        new_obj.write(self.load())
        new_obj.process()
        return new_obj

    def write(self, data):
        """Serialize intermediate data to disk.

        Args:
            * *data* (object): The data

        """
        self.assert_registered()
        self.add_mappings(data)
        filepath = os.path.join(
            config.dir,
            u"intermediate",
            self.filename + u".pickle"
        )
        with open(filepath, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def process_data(self, row):
        """Translate data into correct order"""
        raise NotImplementedError

    def process(self):
        """Process intermediate data from a Python dictionary to a `stats_arrays <https://pypi.python.org/pypi/stats_arrays/>`_ array, which is a `NumPy <http://numpy.scipy.org/>`_ `Structured <http://docs.scipy.org/doc/numpy/reference/generated/numpy.recarray.html#numpy.recarray>`_ `Array <http://docs.scipy.org/doc/numpy/user/basics.rec.html>`_. A structured array (also called record array) is a heterogeneous array, where each column has a different label and data type.

        Processed arrays are saved in the ``processed`` directory.
        """
        data = self.load()
        arr = np.zeros((len(data),), dtype=self.dtype)

        for index, row in enumerate(data):
            values, number = self.process_data(row)
            uncertainties = self.as_uncertainty_dict(number)
            assert len(values) == len(self.dtype_fields)
            assert 'amount' in uncertainties, "Must provide at least `amount` field in `uncertainties`"
            arr[index] = values + (
                uncertainties.get("uncertainty type", 0),
                uncertainties["amount"],
                uncertainties.get("loc", np.NaN),
                uncertainties.get("scale", np.NaN),
                uncertainties.get("shape", np.NaN),
                uncertainties.get("minimum", np.NaN),
                uncertainties.get("maximum", np.NaN),
                uncertainties.get("amount" < 0),
            )
        filepath = os.path.join(
            config.dir,
            u"processed",
            self.filename + u".pickle"
        )
        with open(filepath, "wb") as f:
            pickle.dump(arr, f, protocol=pickle.HIGHEST_PROTOCOL)

    def as_uncertainty_dict(self, value):
        """Convert floats to ``stats_arrays`` uncertainty dict, if necessary"""
        if isinstance(value, dict):
            return value
        try:
            return {'amount': float(value)}
        except:
            raise TypeError(
                "Value must be either an uncertainty dict. or number"
                " (got %s: %s)" % (type(value), value)
            )

    def add_mappings(self, data):
        return

    def validate(self, data):
        """Validate data. Must be called manually.

        Need some metaprogramming because class methods have `self` injected automatically."""
        self.validator.__func__(data)
        return True

    def backup(self):
        """Backup data to compressed JSON file"""
        raise NotImplementedError

