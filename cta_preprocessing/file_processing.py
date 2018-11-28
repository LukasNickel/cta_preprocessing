from .event_processing import event_information
from .event_processing import process_event
from .event_processing import number_of_valid_triggerd_cameras
from ctapipe.io.eventsourcefactory import EventSourceFactory
from ctapipe.calib import CameraCalibrator
from ctapipe.reco.HillasReconstructor import TooFewTelescopesException
import pandas as pd
import fact.io
import pyhessio   ## replace with fact/eventio ?
from tqdm import tqdm
from pathlib import Path


def process_file(input_file,
                 config,
                 return_input_file=False):

    event_source = EventSourceFactory.produce(
        input_url=input_file.as_posix(),
        max_events=config.n_events if config.n_events > 1 else None,
        product='HESSIOEventSource',
    )
    calibrator = CameraCalibrator(
        eventsource=event_source,
        r1_product='HESSIOR1Calibrator',
        extractor_product='NeighbourPeakIntegrator',
    )

    telescope_event_information = []
    array_event_information = []
    for event in tqdm(event_source, disable=config.silent):
        if number_of_valid_triggerd_cameras(event, config) < 2:
            continue

        calibrator.calibrate(event)
        try:
            image_features, reconstruction, _ = process_event(event,
                                                              config
                                                              )
            event_features = event_information(event,
                                               image_features,
                                               reconstruction,
                                               config
                                               )
            array_event_information.append(event_features)
            telescope_event_information.append(image_features)
        except TooFewTelescopesException:
            continue

    telescope_events = pd.concat(telescope_event_information)
    if not telescope_events.empty:
        telescope_events.set_index(['run_id',
                                    'array_event_id',
                                    'telescope_id'],
                                   drop=True,
                                   verify_integrity=True,
                                   inplace=True
                                   )

    array_events = pd.DataFrame(array_event_information)
    if not array_events.empty:
        array_events.set_index(['run_id',
                                'array_event_id'],
                               drop=True,
                               verify_integrity=True,
                               inplace=True
                               )

    run_information = read_simtel_mc_information(input_file) ### TODO: adapt to real data
    df_runs = pd.DataFrame([run_information])
    if not df_runs.empty:
        df_runs.set_index('run_id',
                          drop=True,
                          verify_integrity=True,
                          inplace=True)

    if return_input_file:
        return df_runs, array_events, telescope_events, input_file
    return df_runs, array_events, telescope_events


def verify_file(input_file_path):
    runs = fact.io.read_data(input_file_path.as_posix(), key='runs')   ## same thing with real data
    runs.set_index('run_id', drop=True, verify_integrity=True, inplace=True)

    telescope_events = fact.io.read_data(input_file_path.as_posix(),
                                         key='telescope_events'
                                         )
    telescope_events.set_index(['run_id', 'array_event_id', 'telescope_id'],
                               drop=True,
                               verify_integrity=True,
                               inplace=True
                               )

    array_events = fact.io.read_data(input_file_path.as_posix(),
                                     key='array_events'
                                     )
    array_events.set_index(['run_id', 'array_event_id'],
                           drop=True,
                           verify_integrity=True,
                           inplace=True
                           )

    print('''Processed {} runs,
          {} single telescope events
          and {} array events.'''.format(len(runs),
          len(telescope_events),
          len(array_events)))


def read_simtel_mc_information(simtel_file):
    with pyhessio.open_hessio(simtel_file.as_posix()) as f:
        # do some weird hessio fuckup
        eventstream = f.move_to_next_event()
        _ = next(eventstream)

        d = {
            'mc_spectral_index': f.get_spectral_index(),
            'mc_num_reuse': f.get_mc_num_use(),
            'mc_num_showers': f.get_mc_num_showers(),
            'mc_max_energy': f.get_mc_E_range_Max(),
            'mc_min_energy': f.get_mc_E_range_Min(),
            'mc_max_scatter_range': f.get_mc_core_range_Y(),  # range_X is always 0 in simtel files
            'mc_max_viewcone_radius': f.get_mc_viewcone_Max(),
            'mc_min_viewcone_radius': f.get_mc_viewcone_Min(),
            'run_id': f.get_run_number(),
            'mc_max_altitude': f.get_mc_alt_range_Max(),
            'mc_max_azimuth': f.get_mc_az_range_Max(),
            'mc_min_altitude': f.get_mc_alt_range_Min(),
            'mc_min_azimuth': f.get_mc_az_range_Min(),
        }

        return d


def write_output(runs, array_events, telescope_events, output_file):
    fact.io.write_data(runs,
                       output_file.as_posix(),
                       key='runs',
                       mode='w'
                       )
    fact.io.write_data(array_events,
                       output_file.as_posix(),
                       key='array_events',
                       mode='a'
                       )
    fact.io.write_data(telescope_events,
                       output_file.as_posix(),
                       key='telescope_events',
                       mode='a'
                       )


def output_file_for_input_file(input_file):
    raw_name = Path(input_file.name)
    while raw_name.suffixes:
        raw_name_stem = raw_name.stem
        raw_name = Path(raw_name_stem)
    return(raw_name.with_suffix('.hdf5'))
