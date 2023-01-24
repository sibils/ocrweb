from concurrent.futures import ThreadPoolExecutor
from time import time
import pathlib
import requests


SESSION = requests.Session()

#OCR_SERVICE="http://localhost:8888/ocr/?max_time=7"
OCR_SERVICE="https://ocrweb.text-analytics.ch/ocr/?max_time=7"

#MAX_WORKERS=8

def get_content(filename):
    with open(filename, 'rb') as f:
        return f.read()


output_count = 0

def send_request(content):
    global output_count
    try:
        response = SESSION.post(OCR_SERVICE, data=content, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    except Exception as e:
        print('Exception', e)
    output_count += 1
    result = response.json()
    try:
        print(result)
        if result.get('success'):
            print(output_count)
            with open('out/output_' + str(output_count) + '.json', 'wb') as f:
                f.write(response.content)
        else:
            print('error', response.text)
            pathlib.Path('out/output_' + str(output_count) + '_false.json').touch()
    except Exception as e:
        print(e)


def main():
    l = list(pathlib.Path('images').glob('*.*'))
    # l = ['test.jpg', 'test.png', 'test2.jpg', 'test3.jpg', 'test4.jpg']
    l = [get_content(f) for f in l]
    count = 0

    with ThreadPoolExecutor(max_workers=4) as pool:
        time_before = time()
        for _ in range(0, 1):
            for content in l:
                pool.submit(send_request, content)
                count += 1
    runtime = time() - time_before
    
    print('%s requests, %s second/request, %s seconds in total' % (count, round(runtime / count, 3), runtime))

if __name__ == '__main__':
    main()
