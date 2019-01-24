from .event_processing import event_information
from .event_processing import process_event
from .event_processing import number_of_valid_triggerd_cameras
from ctapipe.io.eventsourcefactory import EventSourceFactory
from ctapipe.io.lsteventsource import LSTEventSource
from ctapipe.calib import CameraCalibrator
from ctapipe.reco.HillasReconstructor import TooFewTelescopesException
from ctapipe.io import SimTelEventSource
import pandas as pd
import fact.io
import eventio
from tqdm import tqdm
from pathlib import Path


def process_data(input_file,
                 config,
                 return_input_file=False):

    event_source = EventSourceFactory.produce(
        input_url=input_file.as_posix(),
        max_events=config.n_events if config.n_events > 1 else None,
        product='LSTEventSource',
    )
    calibrator = CameraCalibrator(
        eventsource=event_source,
        r1_product='NullR1Calibrator',  ## needs to be replaced?
        extractor_product=config.integrator,
    )
    
    df_runs = pd.DataFrame()
    array_events = pd.DataFrame()
    telescope_events = pd.DataFrame()
    if return_input_file:
        return df_runs, array_events, telescope_events, input_file
    return df_runs, array_events, telescope_events


def process_file(input_file,
                 config,
                 return_input_file=False,
                 product='SimTelEventSource'):

    event_source = EventSourceFactory.produce(
        input_url=input_file.as_posix(),
        max_events=config.n_events if config.n_events > 1 else None,
        product=product,
    )

    #event_source.allowed_tels = config.allowed_telescope_ids # if we only want one telescope later

    calibrator = CameraCalibrator(
        eventsource=event_source,
        r1_product='HESSIOR1Calibrator',
        extractor_product=config.integrator,
    )

    telescope_event_information = []
    array_event_information = []
    for event in tqdm(event_source, disable=config.silent):
        if number_of_valid_triggerd_cameras(event, config) < config.min_number_of_valid_triggered_cameras:
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
    with eventio.SimTelFile(simtel_file.as_posix()) as f:
        header = f.mc_run_headers[-1]   # these should all be the same, this is whats suggested by MaxNoe
        d = {
            'mc_spectral_index': header['spectral_index'],
            'mc_num_reuse': header['num_use'],
            'mc_num_showers': header['num_showers'],
            'mc_max_energy': header['E_range'][1],
            'mc_min_energy': header['E_range'][0],
            'mc_max_scatter_range': header['core_range'][1],  # range_X is always 0 in simtel files
            'mc_max_viewcone_radius': header['viewcone'][1],
            'mc_min_viewcone_radius': header['viewcone'][0],
            'run_id': f.header['run'],
            'mc_max_altitude': header['alt_range'][1],
            'mc_max_azimuth': header['az_range'][1],
            'mc_min_altitude': header['alt_range'][0],
            'mc_min_azimuth': header['az_range'][0],
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
