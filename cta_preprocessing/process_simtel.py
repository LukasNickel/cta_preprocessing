import click
from parameters import PREPConfig
import glob
from pathlib import Path
import numpy as np 
from joblib import Parallel, delayed
from file_processing import process_file, verify_file, read_simtel_mc_information
from tqdm import tqdm
import fact.io 




from ctapipe.io.eventsourcefactory import EventSourceFactory
from ctapipe.calib import CameraCalibrator
from ctapipe.image.hillas import hillas_parameters_5, HillasParameterizationError
from ctapipe.image import leakage
from ctapipe.image.cleaning import tailcuts_clean
from ctapipe.reco import HillasReconstructor
from ctapipe.reco.HillasReconstructor import TooFewTelescopesException

from joblib import Parallel, delayed

import pandas as pd
import fact.io
import click
import pyhessio
import numpy as np
from collections import Counter
from tqdm import tqdm
import astropy.units as u
from astropy.coordinates import SkyCoord
import glob
import os
# do some horrible things to silence warnings in ctapipe
import warnings
from astropy.utils.exceptions import AstropyDeprecationWarning





def output_file_for_input_file(input_file):
    raw_name = Path(input_file.name)
    while raw_name.suffixes:
        raw_name_stem = raw_name.stem
        raw_name = Path(raw_name_stem)
    return(input_file.parents[0].joinpath(raw_name.with_suffix('.hdf5')))


@click.command()
@click.argument('input_folder', type=click.Path(dir_okay = True, file_okay=False))
@click.argument('output_folder', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('config_file', type=click.Path(file_okay=True))
def main(input_folder, output_folder, config_file):
    conf_obj = PREPConfig(config_file)


    ##### Fileendungen anpassen !  In Config hinzufügen ?
    input_files = [x for x in Path(input_folder).glob(conf_obj.input_pattern)]
    print(input_files)
    #print(input_files)
    output_files = [output_file_for_input_file(x) for x in input_files]
    print(output_files)
    #print([output_file_for_input_file(x) for x in input_files])
    if not conf_obj.overwrite:
        existing_output = [x.name for x in Path(output_folder).glob('*')]
        print('existing:', existing_output)
        input_files = [x for x in input_files if output_file_for_input_file(x) not in existing_output]
        
    print(input_files)




    print(conf_obj.n_jobs)

    if conf_obj.n_jobs > 1:
         chunksize = conf_obj.chunksize
         n_chunks = (len(input_files) // chunksize) + 1
         chunks = np.array_split(input_files.as_posix(), n_chunks)
         print('test')
         with Parallel(n_jobs=n_jobs, verbose=50) as parallel:
            for chunk in tqdm(chunks):
                results = parallel(delayed(process_file)(f, reco_algorithm=conf_obj.reco_algorithm,
                                                          n_events=n_events, silent=True,
                                                          return_input_file=True)for f in chunk)
                for r in results:
                    runs, array_events, telescope_events, input_file = r

                    if runs is None or array_events is None or telescope_events is None:
                        continue

                    output_file = Path(output_folder).joinpath(output_file_for_input_file(input_file))
                    print(f'processed file {input_file}, writing to {output_file}')

                    fact.io.write_data(runs, output_file.as_posix(), key='runs', mode='w')
                    fact.io.write_data(array_events, output_file.as_posix(), key='array_events', mode='a')
                    fact.io.write_data(telescope_events, output_file.as_posix(), key='telescope_events', mode='a')

                    verify_file(output_file)

    else:
        output_files = list(map(output_file_for_input_file, input_files))
        #output_files = [output_file_for_input_file(x) for x in input_files]
        print('in:', input_files)
        print('out', output_files)
        for input_file, output_file in tqdm(zip(input_files, output_files)):
            print(f'processing file {input_file}, writing to {output_file}')
            print(type(input_file))
            runs, array_events, telescope_events = process_file(input_file.as_posix(), 
                                                                reco_algorithm=conf_obj.reco_algorithm, 
                                                                n_events=conf_obj.n_events)

            if runs is None or array_events is None or telescope_events is None:
                print('file contained no information.')
                continue

            fact.io.write_data(runs, output_file.as_posix(), key='runs', mode='w')
            fact.io.write_data(array_events, output_file.as_posix(), key='array_events', mode='a')
            fact.io.write_data(telescope_events, output_file.as_posix(), key='telescope_events', mode='a')

            verify_file(output_file.as_posix())

if __name__ == '__main__':
    main()






## Kai's main:




# def main(input_pattern, output_folder, n_events, n_jobs, reco_algorithm, overwrite):
#     '''
#     process multiple simtel files gievn as INPUT_FILES into one hdf5 file saved in OUTPUT_FILE.
#     The hdf5 file will contain three groups. 'runs', 'array_events', 'telescope_events'.

#     These files can be put into the classifier tools for learning.
#     See https://github.com/fact-project/classifier-tools

#     '''
#     input_files = glob.glob(input_pattern)
#     print(f'Found {len(input_files)} files.')

#     print(input_files)
#     input_files = [i for i in input_files if i.endswith('simtel.gz')]
#     print(f'Found {len(input_files)} files with "simtel.gz" extension.')

#     if len(input_files) == 0:
#         print(f'No files found. For pattern {input_pattern}. Aborting')
#         return

#     def output_file_for_input_file(input_file):
#         return os.path.join(output_folder, os.path.basename(input_file).replace('simtel.gz', 'hdf5'))

#     if not overwrite:
#         input_files = list(filter(lambda v: not os.path.exists(output_file_for_input_file(v)), input_files))
#         print(f'Preprocessing on {len(input_files)} files that have no matching output')
#     else:
#         print('Preprocessing all found input_files and overwriting existing output.')

#     if n_jobs > 1:
#         chunksize = 50
#         n_chunks = (len(input_files) // chunksize) + 1
#         chunks = np.array_split(input_files, n_chunks)
#         with Parallel(n_jobs=n_jobs, verbose=50) as parallel:
#             for chunk in tqdm(chunks):
#                 results = parallel(delayed(process_file)(f, reco_algorithm=reco_algorithm, n_events=n_events, silent=True, return_input_file=True) for f in chunk)
#                 for r in results:
#                     runs, array_events, telescope_events, input_file = r

#                     if runs is None or array_events is None or telescope_events is None:
#                         continue

#                     output_file = output_file_for_input_file(input_file)
#                     print(f'processed file {input_file}, writing to {output_file}')

#                     fact.io.write_data(runs, output_file, key='runs', mode='w')
#                     fact.io.write_data(array_events, output_file, key='array_events', mode='a')
#                     fact.io.write_data(telescope_events, output_file, key='telescope_events', mode='a')

#                     verify_file(output_file)

#     else:
#         output_files = map(output_file_for_input_file, input_files)

#         for input_file, output_file in tqdm(zip(input_files, output_files)):
#             print(f'processing file {input_file}, writing to {output_file}')
#             runs, array_events, telescope_events = process_file(input_file, reco_algorithm=reco_algorithm, n_events=n_events)

#             if runs is None or array_events is None or telescope_events is None:
#                 print('file contained no information.')
#                 continue

#             fact.io.write_data(runs, output_file, key='runs', mode='w')
#             fact.io.write_data(array_events, output_file, key='array_events', mode='a')
#             fact.io.write_data(telescope_events, output_file, key='telescope_events', mode='a')

#             verify_file(output_file)
