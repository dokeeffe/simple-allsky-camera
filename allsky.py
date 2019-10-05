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
from PIL import Image, ImageDraw, ImageFont 
import numpy as np
from logging.handlers import SysLogHandler
import logging
import ConfigParser

class AllSkyCamera:

    def __init__(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.SysLogHandler(address = '/dev/log')
        formatter = logging.Formatter('%(module)s.%(funcName)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        config = ConfigParser.RawConfigParser()
        config.read(sys.path[0]+'/allsky.cfg')
        self.image_mean = config.getint('AllSky', 'target_image_mean')
        self.min_exposure = config.getint('AllSky', 'min_exposure')
        self.max_exposure = config.getint('AllSky', 'max_exposure')
        self.image_dir = config.get('AllSky', 'image_dir')
        self.zwo_asi_lib = config.get('AllSky', 'zwo_asi_lib')
        self.lower_image_mean = self.image_mean * 0.8
        self.upper_image_mean = self.image_mean * 1.2
        self.inter_exposure_delay_seconds = config.getint('AllSky', 'inter_exposure_delay_seconds')

    def take_exposure(self, camera, filename):
        auto_exp_measurements = []
        try:
            exptime = pickle.load( open( "/tmp/all_sky_exp_time.p", "rb" ) )
        except (IOError):
            logging.warning('Could not load previous exposure time. Setting to min exposure')
            exptime = self.min_exposure
        while True:
            if len(auto_exp_measurements) > 1:
                exptime = self.determine_optimum_exposure(auto_exp_measurements)
            logging.info('Capturing a single 8-bit mono image exposure {} seconds'.format(int(exptime/1000000)))
            camera.set_image_type(asi.ASI_IMG_RAW8)
            camera.set_control_value(asi.ASI_EXPOSURE, exptime)
            camera.capture(filename=filename)
            mean = self.calculate_mean(filename)
            auto_exp_measurements.append([exptime, mean])
            if mean > self.lower_image_mean and mean < self.upper_image_mean:
                logging.info('exposure complete, saving exposure time for next image')
                pickle.dump( exptime, open( "/tmp/all_sky_exp_time.p", "wb" ) )
                self.annotate_image(filename)
                break
            elif len(auto_exp_measurements) < 2:
                exptime = int(exptime * 1.2)

    def annotate_image(self,filename):
        image = Image.open(filename)
        draw  = ImageDraw.Draw(image)
        font  = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', 40)
        draw.text((10,10),'All Sky Camera {}'.format(datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Z %Y UTC")),fill='#ffffff', font=font)
        image.save(filename)


    def calculate_mean(self, image):
        img = Image.open(image).convert("L")
        imgarr = np.array(img)
        return np.mean(imgarr)

    def determine_optimum_exposure(self, auto_exp_measurements):
        x = [float(row[0]) for row in auto_exp_measurements]
        y = [float(row[1]) for row in auto_exp_measurements]
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        exptime = int((self.image_mean- c)/m)
        if exptime > self.max_exposure:
            exptime = self.max_exposure
        logging.info('auto expose determined exp {}'.format(exptime))
        return exptime

    def build_filename(self):
        return '{}/allsky-{}.jpg'.format(self.image_dir, datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S"))

    def main1(self):
        asi.init(self.zwo_asi_lib)
        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            logging.error('No cameras found')
            sys.exit(0)
        camera = asi.Camera(0)
        camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, camera.get_controls()['BandWidth']['MinValue'])
        try:
            while True:
                self.take_exposure(camera, self.build_filename())
                time.sleep(self.inter_exposure_delay_seconds)
        except KeyboardInterrupt:
            print('Manual break by user')
        except asi.ZWO_CaptureError as e:
            logging.error('Error capturing' + str(e))


if __name__ == '__main__':
    cam = AllSkyCamera()
    cam.main1()
