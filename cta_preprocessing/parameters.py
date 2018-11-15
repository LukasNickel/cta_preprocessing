import yaml
import pathlib
import sys


class PREPConfig(object):
    __slots__ = (
        'cleaning_level',
        'names_to_id',
        'types_to_id',
        'allowed_cameras',
        'n_events',
        'n_jobs',
        'reco_algorithm',
        'overwrite',
        'chunksize',
        'silent',
        'verbose',
        'input_pattern',
        'output_suffix',
    )
    def __init__(self, config_file):
        with open(config_file) as config:
            config = yaml.load(config)
        for x in self.__slots__:
            if config.get(x) is not None:
                self.__setattr__(x, config.get(x))
            else:
                raise MissingConfigEntry('PREPConfig.__init__()',
                                         'Missing entry in Config file for: '
                                         + x)


class MissingConfigEntry(Exception):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message =  message
