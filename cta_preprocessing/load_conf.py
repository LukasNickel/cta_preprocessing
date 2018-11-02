import yaml
import click
import configparser
from parameters import PREPConfig

@click.command()
@click.argument('config_file', type=click.Path(file_okay=True))
def main(config_file):
    conf = load_conf(config_file)
    #check_if_set(conf)
    conf_obj = PREPConfig(config_file)
    print(conf_obj.__slots__)
    for x in conf_obj.__slots__:
        if getattr(conf_obj, x) is not None:
            print('True für:', x)
            print(getattr(conf_obj, x))
        else:
            print('False für:', x)

def load_conf(config_file):
    with open(config_file, 'r') as c:
        conf = yaml.load(c)
    return conf

def check_if_set(conf):
    print('cleaning_level' in conf)
    print('LSTCam' in conf)

if __name__ == '__main__':
    main()