# cta_preprocessing

- based upon https://github.com/tudo-astroparticlephysics/cta_preprocessing
- trying to rework process_simtel into an installable command line tool

## Installation:
As of now it is required to manually install ctapipe first.
This will be added to the setup at a later point, but for now refer to 
https://github.com/cta-observatory/ctapipe
for installation of ctapipe.

Everything else can be installed via 
> pip install .
or
> pip install -e .

in the main directory.

## Usage:
Call 
> process_simtel "data_folder" "output_folder" "path_to_config_file"

If you are unsure about what the config file needs to contain take a look at 
> config/sample_config.yaml

Missing entries will lead to the script exiting with an error message telling you to
specify the missing parameter.

## ToDo:
- Rework the whole file handling (+ event_processing) part (ctapipe tablewriter?)
- Find useful default values for all parameters (some are fact based right now instead of cta)
- Dig deeper into cta reconstruction algorithms and cleaning methods
- Test the timing informations that get added during the event processing
- Not directly connected: Improve Compatibility with AICT Tools