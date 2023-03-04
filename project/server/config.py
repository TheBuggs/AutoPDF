#!/usr/bin/python
# -*- coding: utf-8 -*-

class DevelopmentConfig():
    TESTING = False
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = '../uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    FLASK_DEBUG=1

class TestingConfig():
    TESTING = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
