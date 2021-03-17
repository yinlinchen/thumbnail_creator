import boto3
import filetype
import json
import os
import re
import urllib.parse
import uuid

s3_client = boto3.client('s3')


def lambda_handler(event, context):

    bucketName = event['Records'][0]['s3']['bucket']['name']
    InputFile = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    fileToThumbnail(InputFile, bucketName)


def fileToThumbnail(InputFileName, bucketName):

    print("Process file: " + InputFileName)

    ThumbnailFileName = os.path.splitext(
        InputFileName)[0] + os.getenv('EXTENSION')
    print("Output file: " + ThumbnailFileName)

    fileExtension = os.path.splitext(InputFileName)[1]
    print("file extension: " + fileExtension)

    downloadFilePath = '/tmp/' + str(uuid.uuid4()) + fileExtension
    s3_client.download_file(bucketName, InputFileName, downloadFilePath)

    fileType = filetype.guess(downloadFilePath).mime
    print("file type: " + fileType)

    uploadFilePath = '/tmp/' + ThumbnailFileName
    processed = True

    if "application/pdf" in fileType:
        print("Process pdf file: " + downloadFilePath)
        os.system(
            "/opt/bin/convert -density " +
            os.getenv('THUMB_WIDTH') +
            " " +
            downloadFilePath +
            "[0] -quality 90 " +
            uploadFilePath)
    elif "image/" in fileType:
        print("Process image file: " + downloadFilePath)
        os.system(
            "/opt/bin/convert " +
            downloadFilePath +
            " -quiet -resize " +
            str(int( os.getenv('THUMB_WIDTH') ) * 2) +
            "x " +
            uploadFilePath)
    elif "video/" in fileType:
        print("Process video file: " + downloadFilePath)
        os.system(
            "/opt/bin/ffmpeg " +
            "-loglevel error -y -i " +
            downloadFilePath +
            " -vf thumbnail,scale=" +
            str(int( os.getenv('THUMB_WIDTH') ) * 2) +
            ":-1 -frames:v 1 " +
            uploadFilePath)
    else:
        processed = False
        print("This file extension is not supported.")

    if processed:
        s3_client.upload_file(
            uploadFilePath,
            os.getenv('OUTPUT_BUCKET'),
            ThumbnailFileName)
        clearTmpFiles(uploadFilePath, downloadFilePath)
    else:
        os.remove(downloadFilePath)


def clearTmpFiles(uploadFileName, downloadFileName):
    os.remove(uploadFileName)
    os.remove(downloadFileName)
