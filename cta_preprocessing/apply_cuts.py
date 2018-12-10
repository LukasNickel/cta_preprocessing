import click
from pathlib import Path
from .file_processing import output_file_for_input_file
from ctapipe.image.cleaning import number_of_islands
from ctapipe.image.cleaning import fact_image_cleaning


@click.command()
@click.argument('input_file',
                type=click.Path(dir_okay=False, file_okay=True)
                )
@click.argument('output_file',
                type=click.Path(dir_okay=False, file_okay=True)
                )
@click.argument('config_file',
                type=click.Path(file_okay=True)
                )
def main(input_folder, output_folder, config_file):
    config = ImageCleaningConfig(config_file)

    input_path = Path(input_file)
    output_path = Path(output_file)

    
