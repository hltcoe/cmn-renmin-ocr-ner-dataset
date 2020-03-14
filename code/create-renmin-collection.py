import argparse
import os
import subprocess
import sys

"""
Create HLTCOE Renmin OCR/NER Collection by downloading Renmin pdfs and applying them to encoded CoNLL files

2020-03-13
Script must reside in the code directory of the HLTCOE distribution.
Takes a single argument: The name of the directory into which the collection should be placed.
"""

DEFAULT_MAX_TRIES = 3
DEFAULT_THROTTLE = 5

def main():
        
    parser = argparse.ArgumentParser(description='Download and create the HLTCOE Renmin OCR/NER Collection')
    parser.add_argument('--throttle', type=int, help=f'Number of seconds to wait between downloads (default = {DEFAULT_THROTTLE})', default=DEFAULT_THROTTLE)
    parser.add_argument('--tries', type=int, help=f"Number of times to try downloading a given URL before giving up (default = {DEFAULT_MAX_TRIES})", default=DEFAULT_MAX_TRIES)
    parser.add_argument('renmin_dir', help="Directory into which collection should be placed")
    args = parser.parse_args()

    code_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.realpath(os.path.join(code_dir, '..', 'data'))
    downloader = os.path.join(code_dir, "renmin-downloader.py")
    reconstructor = os.path.join(code_dir, "renmin-reconstructor.py")

    # Download the pdf files
    print("Downloading pdf files")
    command = ["python", downloader, "--output", args.renmin_dir, "--throttle", str(args.throttle), "--tries", str(args.tries)]
    result = subprocess.run(command)
    if result.returncode:
        print(f"ERROR: downloader failed with code {result.returncode}")
        sys.exit(result.returncode)

    # Reconstruct each CoNLL file
    for partition in ('train', 'dev', 'test'):
        encoded_file = os.path.join(data_dir, f"{partition}.encoded.txt")
        decoded_file = os.path.join(args.renmin_dir, f"{partition}.conll.txt")
        print(f"Reconstructing {partition} to {decoded_file}")
        command = ["python", reconstructor, args.renmin_dir, encoded_file, decoded_file]
        result = subprocess.run(command)
        if result.returncode:
            print(f"ERROR: reconstructor failed with code {result.returncode}")
            sys.exit(result.returncode)
    print("Success.")

if __name__ == '__main__':
    main()
