import yaml
import os 
dir_path = os.path.dirname(os.path.realpath(__file__))  #Workaround to find sample config, could maybe be done smoother
import pathlib

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
    def __init__(self, config):
        print(dir_path)
        print(pathlib.Path.cwd())
        with open(config) as config, open(dir_path+'/sample_config.yaml') as sample:
            config = yaml.load(config)
            sample = yaml.load(sample)
        for x in self.__slots__:
            if config.get(x) is not None:
                self.__setattr__(x, config.get(x))
            else:
                self.__setattr__(x, sample.get(x))