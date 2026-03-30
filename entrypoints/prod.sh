#!/bin/bash
gunicorn -c ../gunicorn/gunicorn.prod.conf.py core.server:app