#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------
# author      : Ahmet Ozlu
# mail        : ahmetozlu93@gmail.com
# date        : 05.05.2019
# -----------------------------------------

import cv2
from skimage import measure, morphology
from skimage.measure import regionprops
import numpy as np

def extract(sorce_path):
    
    # the parameters are used to remove small size connected pixels outliar 
    constant_parameter_1 = 84
    constant_parameter_2 = 250
    constant_parameter_3 = 100

    # the parameter is used to remove big size connected pixels outliar
    constant_parameter_4 = 18

    # read the input image
    img = cv2.imread(sorce_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.threshold(img, 190, 255, cv2.THRESH_BINARY)[1]
    height, width = img.shape
    # connected component analysis by scikit-learn framework
    blobs = img > img.mean()
    blobs_labels = measure.label(blobs, background=1)
    # image_label_overlay = label2rgb(blobs_labels, image=img)

    the_biggest_component = 0
    total_area = 0
    counter = 0
    average = 0.0
    for region in regionprops(blobs_labels):
        if (region.area > ((width / 210 * height /297 * 2)) / 5):
            total_area = total_area + region.area
            counter = counter + 1

    average = (total_area/counter)

    # experimental-based ratio calculation, modify it for your cases
    # a4_small_size_outliar_constant is used as a threshold value to remove connected outliar connected pixels
    # are smaller than a4_small_size_outliar_constant for A4 size scanned documents
    a4_small_size_outliar_constant = ((average/constant_parameter_1) * constant_parameter_2) + constant_parameter_3

    # experimental-based ratio calculation, modify it for your cases
    # a4_big_size_outliar_constant is used as a threshold value to remove outliar connected pixels
    # are bigger than a4_big_size_outliar_constant for A4 size scanned documents
    a4_big_size_outliar_constant = a4_small_size_outliar_constant * constant_parameter_4

    # remove the connected pixels are smaller than a4_small_size_outliar_constant
    pre_version = morphology.remove_small_objects(blobs_labels, a4_small_size_outliar_constant)
    # remove the connected pixels are bigger than threshold a4_big_size_outliar_constant 
    # to get rid of undesired connected pixels such as table headers and etc.
    component_sizes = np.bincount(pre_version.ravel())
    too_small = component_sizes > (a4_big_size_outliar_constant)
    too_small_mask = too_small[pre_version]
    pre_version[too_small_mask] = 0
    # save the the pre-version which is the image is labelled with colors
    # as considering connected components
    pre_version = pre_version.astype("uint8")
    _, img = cv2.threshold(pre_version, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return img

