import argparse
import time
import arvados
import arvados.collection
import json
import magic
from pathlib import Path
import urllib.request
import socket
import getpass
import sys
sys.path.insert(0,'.')
from bh20sequploader.qc_metadata import qc_metadata
from bh20sequploader.qc_fasta import qc_fasta

ARVADOS_API_HOST='lugli.arvadosapi.com'
ARVADOS_API_TOKEN='2fbebpmbo3rw3x05ueu2i6nx70zhrsb1p22ycu3ry34m4x4462'
UPLOAD_PROJECT='lugli-j7d0g-n5clictpuvwk8aa'

def main():
    parser = argparse.ArgumentParser(description='Upload SARS-CoV-19 sequences for analysis')
    parser.add_argument('sequence', type=argparse.FileType('r'), help='sequence FASTA/FASTQ')
    parser.add_argument('metadata', type=argparse.FileType('r'), help='sequence metadata json')
    args = parser.parse_args()

    api = arvados.api(host=ARVADOS_API_HOST, token=ARVADOS_API_TOKEN, insecure=True)

    target = qc_fasta(args.sequence)

    if not qc_metadata(args.metadata.name):
        print("Failed metadata qc")
        exit(1)

    col = arvados.collection.Collection(api_client=api)

    with col.open(target, "w") as f:
        r = args.sequence.read(65536)
        print(r[0:20])
        while r:
            f.write(r)
            r = args.sequence.read(65536)
    args.sequence.close()

    print("Reading metadata")
    with col.open("metadata.yaml", "w") as f:
        r = args.metadata.read(65536)
        print(r[0:20])
        while r:
            f.write(r)
            r = args.metadata.read(65536)
    args.metadata.close()

    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

    properties = {
        "upload_app": "bh20-seq-uploader",
        "upload_ip": external_ip,
        "upload_user": "%s@%s" % (getpass.getuser(), socket.gethostname())
    }

    col.save_new(owner_uuid=UPLOAD_PROJECT, name="Uploaded by %s from %s" %
                 (properties['upload_user'], properties['upload_ip']),
                 properties=properties, ensure_unique_name=True)

    print("Done")

if __name__ == "__main__":
    main()
