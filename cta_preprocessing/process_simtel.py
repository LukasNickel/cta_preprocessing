import click
from .parameters import PREPConfig
from pathlib import Path
import numpy as np
from joblib import Parallel, delayed
from .file_processing import process_file
from .file_processing import verify_file
from .file_processing import write_output
from .file_processing import output_file_for_input_file
from tqdm import tqdm
import sys


@click.command()
@click.argument('input_folder',
                type=click.Path(dir_okay=True, file_okay=False)
                )
@click.argument('output_folder',
                type=click.Path(dir_okay=True, file_okay=False)
                )
@click.argument('config_file',
                type=click.Path(file_okay=True)
                )
def main(input_folder, output_folder, config_file):
    config = PREPConfig(config_file)

    input_path = Path(input_folder)
    output_path = Path(output_folder)

    input_files = sorted(input_path.glob(config.input_pattern))
    print('Given Files: ', input_files, '\n')

    if not config.overwrite:
        existing_output = [x.name for x in Path(output_folder).glob('*')]
        print('existing:', existing_output, '\n')
        print([output_file_for_input_file(x).name for x in input_files])
        input_files = [x for x in input_files
                       if output_file_for_input_file(x).name not in existing_output]
        print('')

    print('processing: ', input_files, '\n')

    if config.n_jobs > 1:
        chunksize = config.chunksize
        n_chunks = (len(input_files) // chunksize) + 1
        chunks = np.array_split(input_files, n_chunks)

        with Parallel(n_jobs=config.n_jobs,
                      verbose=config.verbose) as parallel:
            for chunk in tqdm(chunks):

                results = parallel(delayed(process_file)
                                          (f,
                                           config,
                                           return_input_file=True)
                                   for f in chunk
                                   )

                for r in results:
                    runs, array_events, telescope_events, input_file = r
                    if any([runs.empty,
                            array_events.empty,
                            telescope_events.empty]
                           ):
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
        for input_file in tqdm(input_files):
            output_file = output_path.joinpath(output_file_for_input_file(input_file))
            print(f'processing file {input_file}, writing to {output_file}')

            results = process_file(input_file,
                                   config,
                                   )

            runs, array_events, telescope_events = results
            if any([runs.empty,
                    array_events.empty,
                    telescope_events.empty]
                   ):
                print('file contained no information.')
                continue

            write_output(runs, array_events, telescope_events, output_file)
            verify_file(output_file)
            print('')


if __name__ == '__main__':
    main()
