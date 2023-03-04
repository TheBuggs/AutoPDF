#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import os
import json
from cv2 import split
from celery.result import AsyncResult, ResultBase
from celery import app as app_celery
from flask import render_template, Blueprint, jsonify, request, redirect, url_for, flash, send_file
from project.server.tasks import upload_task
from werkzeug.utils import secure_filename
from project.server.sign import sign
import uuid
from datetime import datetime, timedelta
import glob
import sqlite3
from sqlite3 import Error

DATABASE = '/usr/src/app/project/db/db.db'

def get_db_connection():
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except Error as e:
        print(e)

    return conn


def create_record(conn, record):
    sql = ''' INSERT INTO records(fid,tid,token,active,fname,fext, created)
              VALUES(?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, record)
    conn.commit()

    return cur.lastrowid


main_blueprint = Blueprint("main", __name__, )


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpeg', 'jpg', 'png'}


@main_blueprint.route("/", methods=["GET"])
def home():
    return render_template("main/home.html")


@main_blueprint.route("/my/<id>", methods=["GET"])
def my(id):
    conn = get_db_connection()
    data = conn.execute(
        'SELECT tid, fid, token FROM records WHERE token LIKE \'' + id + '\' AND active = 1 AND created > datetime(\'now\', \'+2 hour\') ORDER BY created DESC').fetchall()
    conn.close()

    ids = []
    for i in data:
        ids.append((i[0], i[1]))

    return jsonify({"ids": ids}), 202


@main_blueprint.route("/detail/<task_id>", methods=["GET"])
def detail(task_id):
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM records WHERE tid LIKE \'' + task_id + '\'').fetchone()
    conn.close()

    return jsonify({"task": data}), 202


@main_blueprint.route('/delete/<task_id>', methods=['GET'])
def delete_file(task_id):
    sql = 'UPDATE records SET active = 0 WHERE tid LIKE \'' + task_id + '\''
    conn = get_db_connection()

    try:
        conn.execute(sql)
        conn.commit()
    except Error:
        return jsonify({"task": ""}), 202,
    finally:
        conn.close()

    return jsonify({"task": task_id}), 202,


@main_blueprint.route('/upload', methods=['GET', 'POST'])
def upload_file():

    directory = '/usr/src/app/project/uploads/main'

    if not os.path.exists(directory):
        os.mkdir(directory, 777)

    if request.method == 'POST':

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        form = request.form

        if 'user' not in form:
            flash('No user part')
            return redirect(request.url)

        user = form['user']

        name = ""
        if 'fname' in form:
            name = form['fname']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            flash(filename)
            unique = str(uuid.uuid4())
            ext = str(os.path.splitext(filename)[1])
            secure = unique + ext

            if not os.path.exists(directory + '/' + unique):
                os.mkdir(directory + '/' + unique, 777)

            path = os.path.join(directory, unique, secure)
            file.save(path)

            task = upload_task.delay(path, unique, ext)

            conn = get_db_connection()
            created = datetime.now() + timedelta(hours=3)
            record = (unique, task.id, user, 1, name, ext, created)
            create_record(conn, record)
            conn.close()

            return jsonify({"task_id": task.id, "file_id": unique}), 202, {
                'Location': url_for('main.get_status', task_id=task.id, file_id=unique)}


@main_blueprint.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):

    directory = '/usr/src/app/project/uploads/goal'

    if not os.path.exists(directory):
        os.mkdir(directory, 777)

    response = {
        "error": "Missing file"
    }

    if request.method == 'GET':
        dir = os.path.join(directory, file_id)
        files = glob.glob(dir + "/*.pdf")

        if len(files) == 1:

            return send_file(files[0], as_attachment=True)
        if len(files) == 0:

            return jsonify(response), 404

    return jsonify(response), 404


@main_blueprint.route("/tasks/<task_id>/<file_id>", methods=["GET"])
def get_status(task_id, file_id):
    conn = get_db_connection()
    data = conn.execute(
        'SELECT tid, fid, token, fname, fext, created FROM records WHERE tid LIKE \'' + task_id + '\' AND active = 1').fetchone()
    conn.close()

    if not data:
        return jsonify({"error": "miss_data"}), 202

    task = upload_task.AsyncResult(task_id, app=app_celery)

    if not task:
        return jsonify({"error": "miss_task"}), 202

    task_now = datetime.now() + timedelta(hours=3)
    x = data[5].split(".")
    task_created = datetime.strptime(x[0], r'%Y-%m-%d %H:%M:%S')
    minutes = (task_now - task_created).total_seconds() // 60.0
    if task.state == 'PENDING':
        response = {
            "task_id": task_id,
            "file_id": file_id,
            "task_status": 'обработка...',
            "task_result": task.result,
            "task_info": task.info,
            "task_state": task.state,
            "task_real_name": data[3],
            "task_created": minutes,
            "error": "not"
        }
    elif task.state != 'FAILURE':
        response = {
            "task_id": task_id,
            "file_id": file_id,
            "task_status": 'обработен',
            "task_result": task.result,
            "task_info": task.info,
            "task_state": task.state,
            "task_real_name": data[3],
            "task_created": minutes,
            "error": "not"
        }
    elif task.state == 'FAILURE':
        response = {
            "task_id": task_id,
            "file_id": file_id,
            "task_status": 'грешка',
            "task_result": task.result,
            "task_info": task.info,
            "task_state": task.state,
            "task_real_name": data[3],
            "task_created": minutes,
            "error": "not"
        }
    else:
        response = {
            "task_id": task_id,
            "file_id": file_id,
            "task_status": 'грешка',
            "task_result": task.result,
            "task_info": task.info,
            "task_state": task.state,
            "task_real_name": data[3],
            "task_created": minutes,
            "error": "not"
        }
    return jsonify(response), 202
