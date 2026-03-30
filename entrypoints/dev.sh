#!/bin/bash
gunicorn -c ../gunicorn/gunicorn.dev.conf.py core.server:app