import sys
import argparse
import os
import re
from collections import defaultdict

"""
Reconstruct CoNLL files for HLTCOE Renmin OCR/NER Collection with actual tokens given encoded version and Renmin text files

2020-03-13
Run with -h flag for usage information.
"""

class RenminReconstructor:

    def __init__(self, renmin_dir, tokencol, filecol, transduce_fn):
        """
        Create a RenminReconstructor capable of either encoding or decoding a CoNLL file given the corresponding Renmin text files
        """
        self.renmin_dir = renmin_dir
        self.tokencol = tokencol
        self.filecol = filecol
        self.nextkey = defaultdict(int)   # Maps pdf filename to index of next key for that file
        self.filecache = {}
        self.transduce_fn = transduce_fn
        self.index_renmin_dir(renmin_dir)

    def index_renmin_dir(self, renmin_dir):
        """
        Build an index mapping from a date-page string to the corresponding Renmin pdf page
        """
        self.index = {}
        for root, dirs, files in os.walk(renmin_dir):
            for file in filter(lambda x: x.lower().endswith('.pdf'), files):
                rest, month = os.path.split(root)
                ignore, year = os.path.split(rest)
                match = re.match("^(\d\d)-(\d\d)\.pdf", file)
                if not match:
                    continue
                day, page = match.groups()
                key = "_".join((year, month, day, page))
                self.index[key] = os.path.join(root, file)


    def get_encryption_key_text(self, pdf_filename):
        """
        Retrieve the stream text of the specified pdf file, possibly from cache
        """
        if pdf_filename not in self.filecache:
            with open(pdf_filename, 'rb') as infile:
                keytext = b""
                # Select only data between "stream" and "endstream"
                # keywords; everything else is boilerplate, and could
                # allow decoding without access to the original pdf
                in_stream = False
                for line in infile:
                    line = line.rstrip()
                    if line == b"stream":
                        in_stream = True
                    elif line == b"endstream":
                        in_stream = False
                    elif in_stream:
                        keytext += line
                self.filecache[pdf_filename] = keytext
        return(self.filecache[pdf_filename])

    def get_next_code(self, pdf_filename):
        """
        Obtain the next byte value in sequence from the bytes extracted from the pdf file
        """
        crypt_keys = self.get_encryption_key_text(pdf_filename)
        result = crypt_keys[self.nextkey[pdf_filename]]
        self.nextkey[pdf_filename] += 1
        return(result)

    def encode(self, term, pdf_filename):
        """
        Encode a single term by adding its characters' code points to the correct sequence of values from the pdf
        """
        
        return(":".join([str(ord(c) + self.get_next_code(pdf_filename)) for c in term]))
      

    def decode(self, code, pdf_filename):
        """
        Decode a single encoded term by subtracting the correct sequence of values in the pdf stream from the list of ints in the encoded token
        """
        crypt_keys = self.get_encryption_key_text(pdf_filename)
        codenums = code.split(':')
        return("".join([chr(int(x) - self.get_next_code(pdf_filename)) for x in codenums]))

    def transduce(self, source_filename, target_filename):
        """
        Create a new version of the specified tab-separated file, either encoding or decoding the tokens
        """
        with open(source_filename, 'rt') as infile:
            with open(target_filename, 'wt') as outfile:
                for line_num, line in enumerate(infile):
                    line = line.rstrip()
                    if len(line) == 0:
                        outfile.write('\n')
                        continue
                    entries = line.split('\t')
                    entry = entries[self.tokencol]
                    # The name of the original pdf file for this token is encoded in the filecol entry
                    key = entries[self.filecol].split('-')[0][7:]
                    original_pdf_file = self.index[key]
                    if original_pdf_file:
                        replacement = self.transduce_fn(self, entry, original_pdf_file)
                    else:
                        replacement = '***UNKNOWN***'
                        print(f"No source file found for {key}")
                    entries[self.tokencol] = replacement
                    outfile.write("\t".join(entries) + "\n")

def main():
    parser = argparse.ArgumentParser(description='Reconstruct text files from source')
    parser.add_argument('--encode', dest='transduce_fn', action='store_const',
                        const=RenminReconstructor.encode, default=RenminReconstructor.decode,
                        help='encode the data')
    parser.add_argument('--tokencol', default=0, type=int)
    parser.add_argument('--filecol', default=2, type=int)
    parser.add_argument('renmin_dir', help="Base of tree containing text versions of Renmin pages")
    parser.add_argument('source_file', help='CoNLL file to be encoded/decoded')
    parser.add_argument('target_file', help='Output filename')
    args = parser.parse_args()

    reconstructor = RenminReconstructor(args.renmin_dir, args.tokencol, args.filecol, args.transduce_fn)
    reconstructor.transduce(args.source_file, args.target_file)

if __name__ == '__main__':
    main()
