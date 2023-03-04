#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------
# author      : Ahmet Ozlu
# mail        : ahmetozlu93@gmail.com
# date        : 05.05.2019
# -----------------------------------------

import cv2
import os
import fitz
import glob
import shutil
import pytesseract

from matplotlib import pyplot as plt, patches
from pdf2image import convert_from_path
from matplotlib.figure import Figure
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pytesseract import Output
from project.server.extract import extract as extractor

from signature_detect.cropper import Cropper
from signature_detect.extractor import Extractor
from signature_detect.loader import Loader
from signature_detect.judger import Judger


# Store data into folders on current machine
TEMP_PATH = '/usr/src/app/project/uploads/temp/'
GOAL_PATH = '/usr/src/app/project/uploads/goal/'
MAIN_PATH = '/usr/src/app/project/uploads/main/'
LIBR_PATH = '/usr/src/app/project/uploads/libr/'
FONT_PATH = '/usr/src/app/project/server/fonts/'

# Over signature text
TEXT_SM = "чл. 59 \nот ЗЗЛД"
TEXT_LG = "Подписите са заличени на\nоснование чл. 59 от ЗЗЛД\nвъв връзка с чл. 37 от ЗОП"

# Text to RGB
def text_to_rgba(s, *, dpi, **kwargs):
    fig = Figure(facecolor="none")
    fig.text(0, 0, s, **kwargs)
    with BytesIO() as buf:
        fig.savefig(buf, dpi=dpi, format="png", bbox_inches="tight", pad_inches=0)
        buf.seek(0)
        rgba = plt.imread(buf)
    return rgba

# Generate vertical small image with specific text for Bulgarian reasons
def generate_img_vr_sm(save_name):
    img = Image.new('RGB', (36, 30), color = (255, 255, 255))
    font = ImageFont.truetype(FONT_PATH + "Arial-Regular.ttf", size=8)
    d = ImageDraw.Draw(img)
    d.text((2,2), TEXT_SM, font=font, fill=(0, 0, 0))
    img = img.rotate(90, expand=1)
    img.save(save_name)

# Generate horizontal small image with specific text for Bulgarian reasons
def generate_img_hr_sm(save_name):
    img = Image.new('RGB', (36, 30), color = (255, 255, 255))
    font = ImageFont.truetype(FONT_PATH + "Arial-Regular.ttf", size=8)
    d = ImageDraw.Draw(img)
    d.text((2,2), TEXT_SM, font=font, fill=(0, 0, 0))
    img.save(save_name)

# Generate vertical large image with specific text for Bulgarian reasons
def generate_img_vr_lg(save_name):
    img = Image.new('RGB', (100, 40), color = (255, 255, 255))
    font = ImageFont.truetype(FONT_PATH + "Arial-Regular.ttf", size=8)
    d = ImageDraw.Draw(img)
    d.text((2,2), TEXT_LG, font=font, fill=(0, 0, 0))
    img = img.rotate(90, expand=1)
    img.save(save_name)

# Generate horizontal large image with specific text for Bulgarian reasons
def generate_img_hr_lg(save_name):
    img = Image.new('RGB', (100, 40), color = (255, 255, 255))
    font = ImageFont.truetype(FONT_PATH + "Arial-Regular.ttf", size=8)
    d = ImageDraw.Draw(img)
    d.text((2,2), TEXT_LG, font=font, fill=(0, 0, 0))
    img.save(save_name)

# Calc DPI for A4 size image
def calc_dpi(t, w, h):
    if t == "A4":
        f1 = w/8.3
        f2 = h/11.7
        f3 = f1 * f2
        return f3

# Test is file is a PDF document
def is_pdf(path):
    basename = os.path.basename(path)
    dn, dext = os.path.splitext(basename)
    ext = dext[1:].lower()
    if ext == "pdf":
        return True
    return False

# Calc ration for image
def ratio(page, mask) -> tuple[int | float, int | float]:
    sh = mask.shape
    pw = page.rect.width
    ph = page.rect.height
    mw = sh[1]
    mh = sh[0]

    return pw / mw, ph / mh

# Convert PDF to JPEG
def pdf_to_image(path, tp) -> None:
    images = convert_from_path(path)
    for i in range(len(images)):
        images[i].save(tp + str(i) +'.jpg', 'JPEG')

# Convert PDF to TIFF
def pdf_to_tiff(path, tp) -> None:
    mat = fitz.Matrix(210 / 72, 297 / 72)  # sets zoom factor for 100 dpi
    doc = fitz.open(path)
    c = 0
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img_filename = str(c) + ".jpg" #"%04i.tiff"
        img_filename = tp + img_filename
        pix.pil_save(img_filename, format="PNG", dpi=(72,72))
        c += 1

# Remove directory with items inside
def remove(*f) -> None:
    for i in f:
        if os.path.exists(i):
            shutil.rmtree(i)

# Create rect with sizes
def create_rect(x1, x2, y1, y2, w, h):
    x1 = x1 + w
    y1 = y1 + h
    x2 = x2 - w
    y2 = y2 - h
    return fitz.Rect(x1, y1, x2, y2)

# Find hand signatures
def sign(file_path: str, filename: str, ext: str) -> tuple[str | int, int, int, int, str]:

    # Filename must be hashedext
    SECURE_FILENAME = filename

    # All needed directories
    TP  = TEMP_PATH + SECURE_FILENAME + "/"
    GP  = GOAL_PATH + SECURE_FILENAME + "/"
    LIB = LIBR_PATH + SECURE_FILENAME + "/"
    MN =  MAIN_PATH + SECURE_FILENAME + "/"

    # Create temp folder if not exist
    if not os.path.exists(TP):
        os.mkdir(TP, 777)

    # Create goal folder if not exist
    if not os.path.exists(GP):
        os.mkdir(GP, 777)

    # Create main folder if not exist
    if not os.path.exists(LIB):
        os.mkdir(LIB, 777)

    loader  = Loader(low_threshold=(0, 0, 250), high_threshold=(255, 255, 255))
    extract = Extractor(outlier_weight=1, outlier_bias=100, amplfier=10, min_area_size=10)
    cropper = Cropper(min_region_size=200, border_ratio=0)
    judger  = Judger(size_ratio=[1, 4], pixel_ratio=[0.01, 2])

    # Check file is PDF
    is_pdf_file = is_pdf(file_path)

    # Help images with text to over the signature by sizes
    info_page_hr_lg = TP + 'info_hr_lg.jpg'
    info_page_vr_lg = TP + 'info_vr_lg.jpg'
    info_page_hr_sm = TP + 'info_hr_sm.jpg'
    info_page_vr_sm = TP + 'info_hr_sm.jpg'

    # Generate path to final file (Download)
    output_file = GP + SECURE_FILENAME + ext

    # Empty variable for document
    doc = None
    if is_pdf_file:
        # All PDF pages convert to images
        pdf_to_image(file_path, TP)
        # pdf_to_tiff(file_path, TP)
        doc = fitz.open(file_path)
    else:
        # If file is one image save into folder only one file with name 1.jpg
        im = Image.open(file_path)
        im.save(f"{TP}1.jpg")

        # Image to PDF (This is result only we are expected)
        im.save(f"{MN}1.pdf")
        file_path = f"{MN}1.pdf"
        doc = fitz.open(file_path)

    # Pages mask array
    mask = []

    # Sort all pages by names
    files_glob = sorted(glob.glob(TP + "*" ), key=len)

    # Count pages
    cnt = 0

    # Convert to specific size image
    for i in files_glob: 
        image = Image.open(i)
        image.save(TP + str(cnt) + ".jpg") # dpi=(100, 100)
        mask.append(loader.get_masks(TP + str(cnt) + ".jpg"))
        cnt += 1

    # Add negative variable for current page
    is_signed = False

    # Count pages from mask array
    pages = len(mask)

    # Download link to converted file
    link = SECURE_FILENAME

    # Info for count signatures on page
    cnt_signs = 0

    # Info for pages with signatures
    cnt_sign_pages = 0

    # Loop By pages
    for i in range(0, len(mask)):
        f_name = TP + str(i) + ".jpg"
        
        only_sign = extractor(f_name) # custom function get only signature areas
        only_sign = cv2.cvtColor(only_sign, cv2.COLOR_GRAY2RGB)

        cv2.imwrite(f_name, only_sign)

        m = loader.get_masks(f_name)

        im = cv2.imread(files_glob[i])
        image = im.copy()

        axis = None

        # Check page orientation Portland or Landscape
        try:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            orient = pytesseract.image_to_osd(rgb, output_type=Output.DICT)
            axis = orient["orientation"]
        except:
            axis = False

        # Loop By regions
        for j in m:
            
            labeled_mask = extract.extract(j)
            results = cropper.run(j)

            cnt_sign_pages += 1
            
            for result in results.values():
                
                is_signed = judger.judge(result["cropped_mask"])

                # Exist signature on current page
                if is_signed:

                    # Get region for this signature
                    region = result['cropped_region']

                    im = Image.fromarray(result["cropped_mask"])
                    im_file = LIB + str(cnt_sign_pages) + "_" + str(cnt_signs + 1) + ".jpeg"
                    im.save(im_file)   

                    # get left bottom coord for rect
                    ratX, ratY = ratio(doc[i], j)
                    # calc x1 to left bottom coord
                    x1 = round(region[0] * ratX)
                    # calc y1 to left bottom coord
                    y1 = round(region[1] * ratY)
                    # calc width of region
                    w1 = round(region[2] * ratX)
                    # calc high of region
                    h1 = round(region[3] * ratY)
                    # calc x2 coord
                    x2 = x1 + w1
                    # calc y2 coord
                    y2 = y1 + h1
                    
                    sx1 = x1 + w1/8
                    sy1 = y1 + h1/8
                    sx2 = x2 - w1/8
                    sy2 = y2 - h1/8
                    
                    s = [sx1, sy1, sx2, sy2]
                    
                    doc[i].draw_rect(s, fill_opacity=1, fill=(0.98,0.98,0.98))

                    # count to info variable
                    cnt_signs += 1                

                    # check size rectangle and orientation
                    if 45 > axis > 320:

                        if w1 > 100 and h1 > 40:
                            w = (x2 - x1)/2 - 50
                            h = (y2 - y1)/2 - 20
                            x1 = x1 + w
                            y1 = y1 + h
                            x2 = x2 - w
                            y2 = y2 - h
                            rect = fitz.Rect(x1, y1, x2, y2)
                            generate_img_hr_lg(info_page_hr_lg)
                            doc[i].insert_image(rect, filename=info_page_hr_lg)
                        
                        elif 36 < w1 < 100 and  h1 > 30:
                            w = (x2 - x1)/2 - 15
                            h = (y2 - y1)/2 - 15
                            x1 = x1 + w
                            y1 = y1 + h
                            x2 = x2 - w
                            y2 = y2 - h
                            rect = fitz.Rect(x1, y1, x2, y2)
                            generate_img_hr_sm(info_page_hr_sm)
                            doc[i].insert_image(rect, filename=info_page_hr_sm)
                    
                    elif axis and 45 < axis < 320:

                        if w1 > 30 and h1 > 100:
                            w = (x2 - x1)/2 - 20
                            h = (y2 - y1)/2 - 50
                            x1 = x1 + w
                            y1 = y1 + h
                            x2 = x2 - w
                            y2 = y2 - h
                            rect = fitz.Rect(x1, y1, x2, y2)
                            generate_img_vr_lg(info_page_vr_lg)
                            doc[i].insert_image(rect, filename=info_page_vr_lg)
                        elif 36 < h1 < 100 and w1 > 36:
                            w = (x2 - x1)/2 - 15
                            h = (y2 - y1)/2 - 15 
                            x1 = x1 + w
                            y1 = y1 + h
                            x2 = x2 - w
                            y2 = y2 - h
                            rect = fitz.Rect(x1, y1, x2, y2)
                            generate_img_vr_sm(info_page_vr_sm)
                            doc[i].insert_image(rect, filename=info_page_vr_sm)

                    else:

                        if w1 > 100 and h1 > 40:
                            w = (x2 -x1)/2 - 50
                            h = (y2 - y1)/2 - 20
                            x1 = x1 + w
                            y1 = y1 + h
                            x2 = x2 - w
                            y2 = y2 - h
                             
                            rect = fitz.Rect(x1, y1, x2, y2)
                            generate_img_hr_lg(info_page_hr_lg)
                            doc[i].insert_image(rect, filename=info_page_hr_lg)

                        elif 36 < w1 < 100 and h1 > 30:
                            w = (x2 -x1)/2 - 15
                            h = (y2 - y1)/2 - 15
                            x1 = x1 + w
                            y1 = y1 + h
                            x2 = x2 - w
                            y2 = y2 - h
                            rect = fitz.Rect(x1, y1, x2, y2)
                            generate_img_hr_sm(info_page_hr_sm)
                            doc[i].insert_image(rect, filename=info_page_hr_sm)

        if is_pdf_file:
            remove(TEMP_PATH + SECURE_FILENAME, MAIN_PATH + SECURE_FILENAME)
            doc.save(output_file)
    
        return i, pages, cnt_sign_pages, cnt_signs, link
