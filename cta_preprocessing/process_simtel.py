import click
from parameters import PREPConfig

@click.command()
@click.argument('input_folder', type=click.Path(dir_okay = True, file_okay=False))
@click.argument('output_folder', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('config_file', type=click.Path(file_okay=True))
def main(input_folder, output_folder, config_file):
    conf_obj = PREPConfig(config_file)
    for x in conf_obj.__slots__:
        if getattr(conf_obj, x) is not None:
            print('True für:', x)
            print(getattr(conf_obj, x))
        else:
            print('False für:', x)
    print('Input:', input_folder)
    print('Output:', output_folder)


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
