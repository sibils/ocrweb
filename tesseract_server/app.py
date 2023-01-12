import os
import logging
import asyncio
import tempfile
import concurrent.futures
from os.path import dirname, abspath
from typing import Optional
from time import perf_counter

import pytesseract
from fastapi import FastAPI, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


logger = logging.getLogger(__name__)


app = FastAPI(
    docs_url="/",
    openapi_url="/openapi.json",
)


THREAD_COUNT = 5
THREADPOOL = concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_COUNT)
PATTERN_FILE = abspath(dirname(__file__)) + '/eng.pam_patterns'


class OcrResponse(BaseModel):
    success: bool
    ocr_output: str
    """psm 1"""

    ocr_output_alt: str
    """psm 11"""

    request_body_lng: int
    request_path: str
    """Always /"""

    tmpfile: str
    """DEPRECATED"""


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Exception")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'ocr_output': exc.__class__.__module__ + "." + exc.__class__.__name__ + "(" + repr(exc.args) + ")",
                'ocr_output_alt': '',
                'request_body_lng': -1,
                'request_path': '/',
                'tmpfile': 'no available',
            },
        )


app.middleware("http")(catch_exceptions_middleware)


def sync_ocr(image_buffer: bytes, timeout: float = 7) -> OcrResponse:
    # .png, but tesseract deals with any content
    handle, filename = tempfile.mkstemp(prefix='image', suffix='.png')
    try:
        with os.fdopen(handle, 'wb') as fp:
            fp.write(image_buffer)
        lines_1 = pytesseract.image_to_string(filename, timeout=timeout, config=f'--psm 1 --user-patterns {PATTERN_FILE}')
        lines_11 = pytesseract.image_to_string(filename, timeout=timeout, config=f'--psm 11 --user-patterns {PATTERN_FILE}')
        return {
            'success': True,
            'ocr_output': lines_1,
            'ocr_output_alt': lines_11,
            'request_body_lng': len(image_buffer),
            'request_path': '/',
            'tmpfile': 'no available',
        }
    except RuntimeError as re:
        # see https://github.com/madmaze/pytesseract/blob/392fe629cf41229f8ab338a2fb239dff16cd453d/pytesseract/pytesseract.py#L135
        if re.args[0] == 'Tesseract process timeout':
            return {
                'success': False,
                'ocr_output': 'Timeout',
                'ocr_output_alt': '',
                'request_body_lng': -1,
                'request_path': '/',
                'tmpfile': 'no available',
            }
        raise re
    except Exception as e:
        return {
            'success': False,
            'ocr_output': str(e),
            'ocr_output_alt': '',
            'request_body_lng': -1,
            'request_path': '/',
            'tmpfile': 'no available',
        }
    finally:
        os.unlink(filename)


@app.post("/ocr/", description="OCR image using Tesseract")
async def ocr(image_buffer: bytes = Body(), max_time: float = 7.0):
    time_start = perf_counter()
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(THREADPOOL, sync_ocr, image_buffer, max_time)
    runtime = perf_counter() - time_start
    logger.info(f'{len(image_buffer)} bytes parsing in {runtime:} second(s)')
    return result


@app.get('/pool_size', description="""
Maximum number of tesseract processing running at the same time, 
this number may help to configure the client
""")
def pool_size():
    return THREAD_COUNT
