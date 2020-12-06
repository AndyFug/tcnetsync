import setuptools

setuptools.setup(
    name='TcNetSync',
    description='''TC Network Sync library to synchronise SMPTE timecode over TCP/IP.  Requires independent network time
                synchronistion such as NTP''',
    long_description=open('README.md').read(),

    version='0.0.1',
    author='AndyFug',
    license='LICENSE.txt',

    python_requires='>=3.7',
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "timecode",
        "mido",
        "python-rtmidi",
        "timecode_tools @ git+https://git@github.com/AndyFug/timecode_tools.git#egg=timecode_tools",
    ],
    )
