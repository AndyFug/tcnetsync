import setuptools

setuptools.setup(
    name='TC-Network-Sync',
    description='''TC Network Sync library to synchronise SMPTE timecode over LAN.  Requires independent network time
                synchronistion such as NTP''',
    long_description=open('README.txt').read(),

    version='0.0.1',
    author='AndyFug',
    license='LICENSE.txt',

    python_requires='>=3.7',
    packages=setuptools.find_packages(exclude=["test", "test.*"]),
    install_requires=[
       "timecode",
       "mido",
        "python-rtmidi"
    ],
    )
