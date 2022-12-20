import os
import logging
import asyncio
import tempfile
import concurrent.futures
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


THREADPOOL = concurrent.futures.ThreadPoolExecutor(max_workers=5)


class OcrResponse(BaseModel):
    ok: bool
    error: Optional[str]
    text: Optional[str]


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Exception")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": exc.__class__.__module__ + "." + exc.__class__.__name__ + "(" + repr(exc.args) + ")",
            },
        )


app.middleware("http")(catch_exceptions_middleware)


def sync_ocr(image_buffer: bytes) -> OcrResponse:
    # .png, but tesseract deals with any content
    handle, filename = tempfile.mkstemp(prefix='image', suffix='.png')
    try:
        with os.fdopen(handle, 'wb') as fp:
            fp.write(image_buffer)
        lines = pytesseract.image_to_string(filename, timeout=1)
        return {
            'ok': True,
            'text': lines,
        }
    except RuntimeError as re:
        # see https://github.com/madmaze/pytesseract/blob/392fe629cf41229f8ab338a2fb239dff16cd453d/pytesseract/pytesseract.py#L135
        if re.args[0] == 'Tesseract process timeout':
            return {
                'ok': False,
                'error': 'Timeout',
            }
        raise re
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
        }
    finally:
        os.unlink(filename)


@app.post("/ocr/", description="OCR image using Tesseract")
async def ocr(image_buffer: bytes = Body()):
    time_start = perf_counter()
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(THREADPOOL, sync_ocr, image_buffer)
    runtime = perf_counter() - time_start
    logger.info(f'{len(image_buffer)} bytes parsing in {runtime:} second(s)')
    return result
