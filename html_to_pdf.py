#!/usr/bin/python
# -*- coding: utf-8 -*-

import pdfkit
from os import listdir
from os.path import isfile, join, dirname, realpath


def _get_reports_path():
    dir_path = dirname(realpath(__file__))
    return dir_path + '/reports/'


def _get_files_to_convert():
    reports_path = _get_reports_path()
    return [f for f in listdir(reports_path) if isfile(join(reports_path, f))]


def convert_to_pdf():
    files = _get_files_to_convert()
    for in_file in files:
        in_file = _get_reports_path() + in_file
        print in_file
        out_file = in_file[:-5] + '.pdf'
        print out_file
        pdfkit.from_file(in_file, out_file)


def main():
    convert_to_pdf()


if __name__ == '__main__':
    main()
