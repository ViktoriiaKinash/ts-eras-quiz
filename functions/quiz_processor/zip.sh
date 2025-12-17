#!/bin/bash
set -e

ZIP_NAME=quiz_processor.zip
rm -f $ZIP_NAME

zip -r $ZIP_NAME main.py requirements.txt
