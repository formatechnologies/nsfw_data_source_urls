import os
import sys
import signal
import json
import requests
from tqdm import tqdm
import uuid
from hashlib import sha256


DATASET_NAME = 'nsfw2'
INPUT_DIR = '/home/dennis/formatechnologies/nsfw_data_source_urls/raw_data'


DATASETS_DIR = '/home/dennis/storage/dennis/datasets'

DATASET_DIR = os.path.join(DATASETS_DIR, DATASET_NAME)
if not os.path.exists(DATASET_DIR):
    os.mkdir(DATASET_DIR)

DATA_DIR = os.path.join(DATASET_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

PROCESSED_PATH = os.path.join(DATASET_DIR, 'image_processed.json')
if not os.path.exists(PROCESSED_PATH):
    with open(PROCESSED_PATH, 'w') as f:
        json.dump([], f)

HAHES_PATH = os.path.join(DATASET_DIR, 'image_hashes.json')
if not os.path.exists(HAHES_PATH):
    with open(HAHES_PATH, 'w') as f:
        json.dump([], f)


def download_image(url, filename, hashes=[]):
    if os.path.exists(filename):
        return

    try:
        r = requests.get(url)
    except Exception as e:
        print(f'Failed to get {url}: Unknown Error')
        return

    if r.status_code != 200:
        print(f'Failed to get {url}: STATUS CODE {r.status_code}')
        return

    hash_ = sha256(r.content).hexdigest()
    if hash_ in hashes:
        print(f'Failed to get {url}: Duplicate Detected')
        return
    hashes.append(hash_)

    with open(filename, 'wb') as f:
        f.write(r.content)


def load_state():
    with open(PROCESSED_PATH, 'r') as f:
        processed = json.load(f)
    with open(HAHES_PATH, 'r') as f:
        hashes = json.load(f)
    return processed, hashes


def save_state(processed, hashes):
    with open(PROCESSED_PATH, 'w') as f:
        json.dump(processed, f)
    with open(HAHES_PATH, 'w') as f:
        json.dump(hashes, f)


if __name__ == '__main__':
    processed, hashes = load_state()
    def signal_handler(sig, frame):
        save_state(processed, hashes)
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    for cat in tqdm(sorted(os.listdir(INPUT_DIR))):
        print(cat)
        cat_dir = os.path.join(DATA_DIR, cat)
        if not os.path.exists(cat_dir):
            os.mkdir(cat_dir)

        urls_filename = os.path.join(INPUT_DIR, cat, f'urls_{cat}.txt')
        with open(urls_filename) as f:
            urls = sorted([url.strip() for url in f.readlines()])

        uuids_filename = os.path.join(INPUT_DIR, cat, f'uuids_{cat}.json')
        if not os.path.exists(uuids_filename):
            uuids = {url: str(uuid.uuid4()) for url in urls}
            with open(uuids_filename, 'w') as f:
                json.dump(uuids, f, indent=4)
        with open(uuids_filename) as f:
            uuids = json.load(f)

        for i, (url, uuid) in enumerate(tqdm(uuids.items())):
            if uuid in processed:
                continue

            filename = os.path.join(cat_dir, uuid)
            download_image(url, filename, hashes)
            processed.append(uuid)

            if i % 100 == 0 or i == len(uuids) - 1:
                save_state(processed, hashes)
