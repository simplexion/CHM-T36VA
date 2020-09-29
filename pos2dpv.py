#!/usr/bin/env python3

from argparse import ArgumentParser
from logging import debug, info, warning, error, basicConfig as logConfig
from logging import DEBUG, INFO, WARNING, ERROR
from datetime import datetime
from os import path
import csv
from jinja2 import Template

def parse_arguments():
    parser = ArgumentParser(
        description="Python CLI Template",
        epilog="")
    
    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument("-q", "--quiet",   action="store_true", help="turn off warnings")
    verbose.add_argument("-v", "--verbose", action="count",      help="set verbose loglevel")

    parser.add_argument('-f', '--feeder_setup_file', type=str, required=True, help='Feeder definition csv file.')
    parser.add_argument('-p', '--pos_file',          type=str, required=True, help='KiCad POS file.')
    parser.add_argument('-d', '--dpv_file',          type=str, required=True, help='PnP file.')

    args = parser.parse_args()
    return args

def configure_logging(verbose, quiet):
    log_level = ERROR   if quiet else \
                WARNING if not verbose else \
                INFO    if 1 == verbose else \
                DEBUG   #  2 <= verbose
    logConfig(format="%(asctime)-15s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log_level)
    debug("DEBUG Log Level")

def csv_to_dict_list(csv_file_path):
    # function to automatically turn strings into python values
    def auto_type(value):
        result = value
        if '' == value:
            result = None
        if value.upper() in ('Y', 'T') :
            result = True
        elif value.upper() in ('N', 'F'):
            result = False
        elif value.isnumeric():
            result = int(value, 0)
        else:
            try:
                result = float(value)
            except ValueError:
                pass
        return result
    # read csv file and turn into list of python dicts
    with open(csv_file_path, 'r') as csv_file:
        return [{k: auto_type(v) for k, v in row.items()} for row in csv.DictReader(csv_file)]

def find_feeder(feeders, component):
    result = None
    # concact value and package to component name
    component_identifiers = (component["Val"], component["Package"])
    component_name = "-".join((str(identifier) for identifier in component_identifiers if identifier))
    # try to find matching feeder
    for feeder in feeders:
        # concat component and aliases of feeder
        feeder_component_names = [feeder["Component"]]
        if feeder["Aliases"]:
            feeder_component_names += feeder["Aliases"].split(":")
        # match
        if component_name in feeder_component_names:
            result = feeder
    return result

def main(args):
    now = datetime.now()
    fiducials = list()
    placements = list()
    unplaced = list()
    # read in files
    components = csv_to_dict_list(args.pos_file)
    feeders = csv_to_dict_list(args.feeder_setup_file)
    # filter out unused feeders
    feeders = [feeder for feeder in feeders if feeder["Component"]]
    # assign each component to a feeder in a placement
    for component in components:
        if component["Ref"].startswith("FID"):
            fiducials += [component]
        else:
            feeder = find_feeder(feeders, component)
            if feeder:
                # correct tape orientation (mounted 90 degrees from the board)
                component["Rot"] -= 90
                # add an angle compensation to this component
                component["Rot"] += feeder["Relative Tape Angle"]
                # Correct rotations from -180 to 180
                component["Rot"] = ((component["Rot"]+180)%360)-180
                placements += [{"component": component, "feeder":feeder}]
            else:
                unplaced += [component]
    # print for inspection
    for placement in placements:
        info("Using feeder {} for {}".format(placement["feeder"]["Feeder Index"], placement["component"]["Ref"]))
    for fiducial in fiducials:
        info("Fiducial {} at ({}, {})".format(fiducial["Ref"], fiducial["PosX"], fiducial["PosY"]))
    warning("Not placing {}".format(", ".join([component["Ref"] for component in unplaced])))
    # fill variables for jinja template
    header = {
        "file": path.basename(args.dpv_file),
        "pcbfile": path.basename(args.pos_file),
        "date": "{:02d}/{:02d}/{:02d}".format(now.year, now.month, now.day),
        "time": "{:02d}:{:02d}:{:02d}".format(now.hour, now.minute, now.second),
        "paneltype": 0,
    }

    stations = [
        {
            "id": feeder["Feeder Index"],
            "delt_x": feeder["XOffset"],
            "delt_y": feeder["YOffset"],
            "feed_rates": feeder["Feed Spacing"],
            "note": feeder["Component"],
            "height": feeder["Height"],
            "speed": feeder["Speed"],
            "status": sum(
                [
                    0b001 if not feeder["Place Component"] else 0,
                    0b010 if feeder["Check Vacuum"] else 0,
                    0b100 if feeder["Use Vision"] else 0,
                ]
            ),
            "size_x": 0,
            "size_y": 0,
            "height_take": 0,
            "delay_take": 0,
        } for feeder in feeders
    ]

    ecomponents = [
        {
            "p_head": feeder["Head"],
            "s_t_no": feeder["Feeder Index"],
            "delt_x": component["PosX"],
            "delt_y": component["PosY"],
            "angle": component["Rot"],
            "height": feeder["Height"],
            "skip":sum(
                [
                    0b001 if not feeder["Place Component"] else 0,
                    0b010 if feeder["Check Vacuum"] else 0,
                    0b100 if feeder["Use Vision"] else 0,
                ]
            ),
            "speed": feeder["Speed"],
            "explain": component["Ref"],
            "note": feeder["Component"],
            "delay": 0,
        } for feeder, component in [[placement["feeder"], placement["component"]] for placement in placements]
    ]

    calib_points = [
        {
            "offset_x": fiducial["PosX"],
            "offset_y": fiducial["PosY"],
            "note": fiducial["Ref"],
        } for fiducial in fiducials
    ]

    with open(args.dpv_file, 'w') as dpv:
        with open('template.dpv.j2', 'r') as f:
            template = Template(f.read())
        dpv.write(template.render(header=header, stations=stations, ecomponents=ecomponents, calib_points=calib_points))

if "__main__" == __name__:
    args = parse_arguments()
    configure_logging(args.verbose, args.quiet)
    main(args)
