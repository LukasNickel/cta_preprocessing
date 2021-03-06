import yaml

# inheritage from CONFIG?

class PREPConfig(object):
    __slots__ = (
        'names_to_id',
        'types_to_id',
        'allowed_cameras',
        'n_events',
        'n_jobs',
        'reco_algorithm',
        'cleaning_method',
        'overwrite',
        'chunksize',
        'silent',
        'verbose',
        'input_pattern',
        'output_suffix',
        'cleaning_level',
        'min_num_islands',
        'min_width',
        'min_length',
        'integrator',
        'min_number_of_valid_triggered_cameras',
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
    """Exception raised for missing entries in the given config file.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
