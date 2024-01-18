#!/usr/bin/env python

import sys
import argparse

import idronaut_parser

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=argparse.FileType("r"), nargs="+", help="idronaut file(s) to parse")
    parser.add_argument("--csvfile", required=True)
    args = parser.parse_args()

    idro_parser = idronaut_parser.IdronautParser()

    for file_ in args.file:
        print(f"Reading file at {file_.name}")
        idro_parser.read_file(file_)

    idro_parser.output_csv_data(args.csvfile)
    return 0

if __name__ == "__main__":
    sys.exit(main())



