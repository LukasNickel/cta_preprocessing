from ctapipe.image.hillas import hillas_parameters
from ctapipe.image.hillas import HillasParameterizationError
from ctapipe.image import leakage
from ctapipe.image.cleaning import tailcuts_clean
from ctapipe.image.cleaning import fact_image_cleaning
from ctapipe.image.cleaning import number_of_islands
from ctapipe.image.timing_parameters import timing_parameters
from ctapipe.reco import HillasReconstructor
from ctapipe.reco import hillas_intersection as HillasIntersection  # ??

import pandas as pd
import numpy as np
from collections import Counter

import astropy.units as u
from astropy.coordinates import SkyCoord


def event_information(event, image_features, reconstruction, config):
    counter = Counter(image_features.telescope_type_name)
    d = {
        'mc_alt': event.mc.alt,
        'mc_az': event.mc.az,
        'mc_core_x': event.mc.core_x,
        'mc_core_y': event.mc.core_y,
        'mc_x_max': event.mc.x_max.to(u.g / u.cm**2).value,
        'num_triggered_telescopes': number_of_valid_triggerd_cameras(event,
                                                                     config),
        'mc_height_first_interaction': event.mc.h_first_int,
        'mc_energy': event.mc.energy.to('TeV').value,
        'mc_corsika_primary_id': event.mc.shower_primary_id,
        'run_id': event.r0.obs_id,
        'array_event_id': event.dl0.event_id,
        'alt_prediction': reconstruction.alt.si.value,
        'az_prediction': reconstruction.az.si.value,
        'core_x_prediction': reconstruction.core_x,
        'core_y_prediction': reconstruction.core_y,
        'h_max_prediction': reconstruction.h_max,
        'total_intensity': image_features.intensity.sum(),
        'num_triggered_lst': counter['LST'],
        'num_triggered_mst': counter['MST'],
        'num_triggered_sst': counter['SST'],
    }

    return {k: strip_unit(v) for k, v in d.items()}


def process_event(event, config):
    '''
    Processes
    '''

    reco_algorithm = config.reco_algorithm
    features = {}
    params = {}

    pointing_azimuth = {}
    pointing_altitude = {}

    tel_x = {}
    tel_y = {}
    tel_focal_lengths = {}
    cleaning_method = config.cleaning_method
    valid_cleaning_methods = ['tailcuts_clean', 'fact_image_cleaning']
    if cleaning_method not in valid_cleaning_methods:
        print('Cleaning Method not implemented')
        print('Please use one of ', valid_cleaning_methods)
        return None

    for telescope_id, dl1 in event.dl1.tel.items():
        camera = event.inst.subarray.tels[telescope_id].camera
        if camera.cam_id not in config.allowed_cameras:
            continue

        telescope_type_name = event.inst.subarray.tels[telescope_id].optics.tel_type

        if cleaning_method == 'tailcuts_clean':
            boundary_thresh, picture_thresh, min_number_picture_neighbors = config.cleaning_level[camera.cam_id]
            mask = tailcuts_clean(
                camera,
                dl1.image[0],
                *config.cleaning_level[camera.cam_id]
            )

        elif cleaning_method == 'fact_image_cleaning':
            mask = fact_image_cleaning(
                camera,
                dl1.image[0],
                *config.cleaning_level_fact[camera.cam_id]
            )

        try:
            cleaned = dl1.image[0].copy()
            cleaned[~mask] = 0
            hillas_container = hillas_parameters(
                camera,
                cleaned,
            )
            params[telescope_id] = hillas_container
        except HillasParameterizationError:
            continue
        # probably wise to add try...except blocks here as well
        # Add more Features here (look what ctapipe can do, timing?)
        num_islands, island_labels = number_of_islands(camera, mask)
        island_dict = {'num_islands': num_islands, 
                       'island_labels': island_labels}
        leakage_container = leakage(camera, dl1.image[0], mask)
        timing_container = timing_parameters(camera, dl1.image[0],
                                             dl1.peakpos[0], hillas_container)
        

        pointing_azimuth[telescope_id] = event.mc.tel[telescope_id].azimuth_raw * u.rad
        pointing_altitude[telescope_id] = event.mc.tel[telescope_id].altitude_raw * u.rad
        tel_x[telescope_id] = event.inst.subarray.positions[telescope_id][0]
        tel_y[telescope_id] = event.inst.subarray.positions[telescope_id][1]

        telescope_description = event.inst.subarray.tel[telescope_id]
        tel_focal_lengths[telescope_id] = telescope_description.optics.equivalent_focal_length

        d = {
            'array_event_id': event.dl0.event_id,
            'telescope_id': int(telescope_id),
            'camera_name': camera.cam_id,
            'camera_id': config.names_to_id[camera.cam_id],
            'run_id': event.r0.obs_id,
            'telescope_type_name': telescope_type_name,
            'telescope_type_id': config.types_to_id[telescope_type_name],
            'pointing_azimuth': event.mc.tel[telescope_id].azimuth_raw,
            'pointing_altitude': event.mc.tel[telescope_id].altitude_raw,
            'mirror_area': telescope_description.optics.mirror_area,
            'focal_length': telescope_description.optics.equivalent_focal_length,
        }

        d.update(hillas_container.as_dict())
        d.update(leakage_container.as_dict())
        d.update(island_dict)
        d.update(timing_container.as_dict())

        features[telescope_id] = ({k: strip_unit(v) for k, v in d.items()})

    if reco_algorithm == 'intersection':
        reco = HillasIntersection()
        array_direction = SkyCoord(alt=event.mcheader.run_array_direction[1],
                                   az=event.mcheader.run_array_direction[0],
                                   frame='altaz'
                                   )
        reconstruction = reco.predict(params,
                                      tel_x,
                                      tel_y,
                                      tel_focal_lengths,
                                      array_direction
                                      )
    elif reco_algorithm == 'planes':
        reco = HillasReconstructor()
        reconstruction = reco.predict(params,
                                      event.inst,
                                      pointing_altitude,
                                      pointing_azimuth
                                      )

    for telescope_id in event.dl1.tel.keys():
        if telescope_id not in params:
            continue
        camera = event.inst.subarray.tels[telescope_id].camera
        if camera.cam_id not in config.allowed_cameras:
            continue

        pos = event.inst.subarray.positions[telescope_id]
        x, y = pos[0], pos[1]
        core_x = reconstruction.core_x
        core_y = reconstruction.core_y
        d = np.sqrt((core_x - x)**2 + (core_y - y)**2)
        features[telescope_id]['distance_to_core'] = d.value

    return pd.DataFrame(list(features.values())), reconstruction, params


def number_of_valid_triggerd_cameras(event, config):
    triggerd_tel_ids = event.trig.tels_with_trigger
    triggerd_camera_names = [event.inst.subarray.tels[i].camera.cam_id
                             for i in triggerd_tel_ids]
    valid_triggered_cameras = list(filter(lambda c:
                                          c in
                                          config.allowed_cameras,
                                          triggerd_camera_names))
    return len(valid_triggered_cameras)


def strip_unit(v):
    try:
        return v.si.value
    except AttributeError:
        return v
