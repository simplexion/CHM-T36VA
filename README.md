# CHM-T36VA
Central Repository for Configuration and other Files regarding the Charmhigh CHM-T36VA Desktop Pick and Place Machine

## Script

### `./pos2dpv.py`
A script for converting KiCad *.pos* files to *.dpv* files.

#### Usage
```
usage: pos2dpv.py [-h] [-q | -v] -f FEEDER_SETUP_FILE -p POS_FILE -d DPV_FILE

Python CLI Template

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           turn off warnings
  -v, --verbose         set verbose loglevel
  -f FEEDER_SETUP_FILE, --feeder_setup_file FEEDER_SETUP_FILE
                        Feeder definition csv file.
  -p POS_FILE, --pos_file POS_FILE
                        KiCad POS file.
  -d DPV_FILE, --dpv_file DPV_FILE
                        PnP file.
```

#### Example
```bash
./pos2dpv.py -f feeders_setup.csv -p top-pos.csv -d top-pos.dpv -v
```

