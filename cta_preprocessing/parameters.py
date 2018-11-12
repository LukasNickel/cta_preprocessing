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
        sample_file = pathlib.Path(sys.path[0] + '/sample_config.yaml')
        with open(config_file) as config, open(sample_file) as sample:
            config = yaml.load(config)
            sample = yaml.load(sample)
        for x in self.__slots__:
            if config.get(x) is not None:
                self.__setattr__(x, config.get(x))
            else:
                self.__setattr__(x, sample.get(x))