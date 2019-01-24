from setuptools import setup, find_packages

setup(
    name='cta_preprocessing',
    version='0.13',
    description='Preprocessing steps for CTA Data',
    url='https://github.com/LukasNickel/cta_preprocessing',
    author='Kai Brügge, Lukas Nickel',
    author_email='lukas.nickel@tu-dortmund.de',
    license='MIT',
    packages=find_packages(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[   # also needs ctapipe installed
        'astropy',
        'click',
        'h5py',
        'joblib',
        'matplotlib>=2.0',  # in anaconda
        'numpy',            # in anaconda
        'pandas',           # in anaconda
        'pyfact>=0.16.0',
        'pyyaml',             # in anaconda
        'tqdm',
        'eventio',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'process_simtel = cta_preprocessing.process_simtel:main',
            'merge_files = cta_preprocessing.merge_files:main',
        ],
    }
)
