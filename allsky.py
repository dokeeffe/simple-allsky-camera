#!/usr/bin/env python

#
# copy the asi lib so file and set the ZWO_ASI_LIB env var to point to it
# copy the asi udev rules from the dev package so the camera can be opened as non root `sudo install asi.rules /lib/udev/rules.d`
#

import sys, os, time
import zwoasi as asi
import pickle
import datetime
import PIL
import numpy as np
import math
from ConfigParser import SafeConfigParser
from logging.handlers import SysLogHandler
import logging
import ConfigParser

class AllSkyCamera:

    def __init__():
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.SysLogHandler(address = '/dev/log')
        formatter = logging.Formatter('%(module)s.%(funcName)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        config = ConfigParser.RawConfigParser()
        config.read('allsky.cfg')
        self.image_mean = config.getint('AllSky', 'target_image_mean')
        self.min_exposure = config.getint('AllSky', 'min_exposure')
        self.max_exposure = config.getint('AllSky', 'max_exposure')
        self.image_dir = config.getint('AllSky', 'image_dir')
        self.lower_image_mean = self.image_mean * 0.8
        self.upper_image_mean = self.image_mean * 1.2
        self.inter_exposure_delay_seconds = config.getint('AllSky', 'inter_exposure_delay_seconds')

    def take_exposure(camera):
        auto_exp_measurements = []
        try:
            exptime = pickle.load( open( "/tmp/all_sky_exp_time.p", "rb" ) )
        except (IOError):
            logging.warn('Could not load previous exposure time. Setting to min exposure')
            exptime = minexp
        while True:
            if len(auto_exp_measurements) > 1:
                exptime = determine_optimum_exposure(auto_exp_measurements)
            logging.info('Capturing a single 8-bit mono image exposure {} seconds'.format(int(exptime/1000000)))
            camera.set_image_type(asi.ASI_IMG_RAW8)
            camera.set_control_value(asi.ASI_EXPOSURE, exptime)
            camera.capture(filename=filename)
            mean = calculate_mean(filename)
            auto_exp_measurements.append([exptime, mean])
            if mean > LOWER_IMAGE_MEAN and mean < UPPER_IMAGE_MEAN:
                logging.info('exposure complete, saving exposure time for next image')
                pickle.dump( exptime, open( "/tmp/all_sky_exp_time.p", "wb" ) )
                break
            elif len(auto_exp_measurements) < 2:
                exptime = int(exptime * 1.2)

    def calculate_mean(image):
        img = PIL.Image.open(image).convert("L")
        imgarr = np.array(img)
        return np.mean(imgarr)

    def determine_optimum_exposure(auto_exp_measurements):
        self.logging.info
        x = [float(row[0]) for row in auto_exp_measurements]
        y = [float(row[1]) for row in auto_exp_measurements]
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        exptime = int((DESIRED_IMAGE_MEAN-c)/m)
        if exptime > MAX_EXPOSURE:
            exptime = MAX_EXPOSURE
        logging.info('auto expose determined exp {}'.format(exptime))
        return exptime

    def main1():
        filename = '{}/allsky-{}.jpg'.format(self.image_dir, datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S"))
        env_filename = os.getenv('ZWO_ASI_LIB')
        asi.init(env_filename)
        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            logging.error('No cameras found')
            sys.exit(0)
        camera = asi.Camera(0)
        camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, camera.get_controls()['BandWidth']['MinValue'])
        minexp, maxexp = MIN_EXPOSURE, MAX_EXPOSURE
        try:
            while True:
                take_exposure(camera)
                time.sleep(self.inter_exposure_delay_seconds)
        except KeyboardInterrupt:
            print('Manual break by user')
        except asi.ZWO_CaptureError:


if __name__ == '__main__':
    cam = AllSkyCamera()
    cam.main1()
