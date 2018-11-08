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
warnings.filterwarnings('ignore', category=AstropyDeprecationWarning, append=True)
warnings.filterwarnings('ignore', category=FutureWarning, append=True)
np.warnings.filterwarnings('ignore')



from event_processing import *

## AUSSORTIEREN!!


def process_file(input_file, reco_algorithm, n_events=-1, silent=False, return_input_file=False):
    print(input_file)
    print(type(input_file))

    event_source = EventSourceFactory.produce(
        input_url=input_file,
        max_events=n_events if n_events > 1 else None,
        product='HESSIOEventSource',
    )
    calibrator = CameraCalibrator(
        eventsource=event_source,
        r1_product='HESSIOR1Calibrator',
        extractor_product='NeighbourPeakIntegrator',
    )

    telescope_event_information = []
    array_event_information = []
    for event in tqdm(event_source, disable=silent):
        if number_of_valid_triggerd_cameras(event) < 2:
            continue

        calibrator.calibrate(event)
        try:
            image_features, reconstruction, _ = process_event(event, reco_algorithm=reco_algorithm)
            event_features = event_information(event, image_features, reconstruction)
            array_event_information.append(event_features)
            telescope_event_information.append(image_features)
        except TooFewTelescopesException:
            continue

    if (len(telescope_event_information) == 0):
        if return_input_file:
            return None, None, None, None
        return None, None, None

    telescope_events = pd.concat(telescope_event_information)
    telescope_events.set_index(['run_id', 'array_event_id', 'telescope_id'], drop=True, verify_integrity=True, inplace=True)

    array_events = pd.DataFrame(array_event_information)
    array_events.set_index(['run_id', 'array_event_id'], drop=True, verify_integrity=True, inplace=True)

    run_information = read_simtel_mc_information(input_file)
    df_runs = pd.DataFrame([run_information])
    df_runs.set_index('run_id', drop=True, verify_integrity=True, inplace=True)

    if return_input_file:
        return df_runs, array_events, telescope_events, input_file
    return df_runs, array_events, telescope_events


def verify_file(input_file_path):
    runs = fact.io.read_data(input_file_path, key='runs')
    runs.set_index('run_id', drop=True, verify_integrity=True, inplace=True)

    telescope_events = fact.io.read_data(input_file_path, key='telescope_events')
    telescope_events.set_index(['run_id', 'array_event_id', 'telescope_id'], drop=True, verify_integrity=True, inplace=True)

    array_events = fact.io.read_data(input_file_path, key='array_events')
    array_events.set_index(['run_id', 'array_event_id'], drop=True, verify_integrity=True, inplace=True)

    print('Processed {} runs, {} single telescope events and {} array events.'.format(len(runs), len(telescope_events), len(array_events)))


def read_simtel_mc_information(simtel_file):
    with pyhessio.open_hessio(simtel_file) as f:
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
