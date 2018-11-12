import click
from parameters import PREPConfig
from pathlib import Path
import numpy as np
from joblib import Parallel, delayed
from file_processing import process_file
from file_processing import verify_file
from file_processing import write_output
from tqdm import tqdm
import sys
# do some horrible things to silence warnings in ctapipe
# import warnings
# from astropy.utils.exceptions import AstropyDeprecationWarning


def output_file_for_input_file(input_file):
    raw_name = Path(input_file.name)
    while raw_name.suffixes:
        raw_name_stem = raw_name.stem
        raw_name = Path(raw_name_stem)
    return(raw_name.with_suffix('.hdf5'))


@click.command()
@click.argument('input_folder',
                type=click.Path(dir_okay=True, file_okay=False)
                )
@click.argument('output_folder',
                type=click.Path(dir_okay=True, file_okay=False)
                )
@click.argument('config_file',
                default=Path(sys.path[0]+'/sample_config.yaml'),
                type=click.Path(file_okay=True)
                )
def main(input_folder, output_folder, config_file):
    config = PREPConfig(config_file)

    input_path = Path(input_folder)
    output_path = Path(output_folder)

    input_files = sorted(input_path.glob(config.input_pattern))
    print(input_files)

    output_files = [output_path.joinpath(output_file_for_input_file(x))
                    for x in input_files]
    print(output_files)

    if not config.overwrite:
        existing_output = [x.name for x in Path(output_folder).glob('*')]
        print('existing:', existing_output)
        input_files = [x for x in input_files
                       if output_file_for_input_file(x) not in existing_output]

    if config.n_jobs > 1:
        chunksize = config.chunksize
        n_chunks = (len(input_files) // chunksize) + 1
        chunks = np.array_split(input_files, n_chunks)

        with Parallel(n_jobs=config.n_jobs, verbose=config.verbose) as parallel:
            for chunk in tqdm(chunks):

                results = parallel(delayed(process_file)
                                          (f,
                                           reco_algorithm=config.reco_algorithm,
                                           n_events=config.n_events,
                                           silent=config.silent,
                                           return_input_file=True)
                                   for f in chunk
                                   )

                for r in results:
                    runs, array_events, telescope_events, input_file = r
                    if runs is None or array_events is None or telescope_events is None:
                        print('file contained no information.')
                        continue

                    output_file = output_path.joinpath(output_file_for_input_file(input_file))
                    print(f'''processed file {input_file},
                          writing to {output_file}'''
                          )
                    write_output(runs, array_events,
                                 telescope_events,
                                 output_file)
                    verify_file(output_file)

    else:
        for input_file, output_file in tqdm(zip(input_files, output_files)):
            print(f'processing file {input_file}, writing to {output_file}')

            results = process_file(input_file,
                                   reco_algorithm=config.reco_algorithm,
                                   n_events=config.n_events
                                   )

            runs, array_events, telescope_events = results
            # if any in [runs, array_events, telescope_events] is None:
            if runs is None or array_events is None or telescope_events is None:
                print('file contained no information.')
                continue

            write_output(runs, array_events, telescope_events, output_file)
            verify_file(output_file)


if __name__ == '__main__':
    main()
