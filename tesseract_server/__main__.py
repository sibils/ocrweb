import argparse
from os import path

import uvicorn
import uvicorn.config


def parse_args(app_name = ""):
    parser = argparse.ArgumentParser(description=app_name)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--production', dest='production', action='store_true',
                       help='Run in production mode')
    group.add_argument('--profile', type=str, dest='profile_filename',
                       help='Run cProfile in developpment mode and record the a .prof file',
                       default=None)
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Bind socket to this host.    [default: 127.0.0.1]')
    parser.add_argument('--port', type=int, default=8888,
                       help='Bind socket to this port.    [default: 8888]')
    parser.add_argument('--root-path', type=str, default='/',
                       help='Set the root_path for applications submounted below a given URL path.')
    parser.add_argument('--workers', type=int, default=5,
                        help='Number of tesseract workers [5]')
    return parser.parse_args()


def get_reload_excludes():
    if path.exists('.gitignore'):
        with open('.gitignore') as f:
            for file_name in f.readlines():
                yield file_name.replace('\n', '')


def run_uvicorn(app_name, args):
    import logging

    uvicorn_kwargs = dict(
        host=args.host,
        port=args.port,
        root_path=args.root_path,
        access_log=True,
    )

    if args.production:
        logging.basicConfig(level=logging.INFO)
        uvicorn.config.LOGGING_CONFIG['formatters']['default']['fmt'] = '%(asctime)-15s | %(process)d | %(levelname)s | %(name)s | %(message)s'
        uvicorn.config.LOGGING_CONFIG['formatters']['access']['fmt'] =  '%(asctime)-15s | %(process)d | %(levelprefix)s | %(client_addr)s | "%(request_line)s" %(status_code)s'
        uvicorn.run(
            app_name,
            workers = 1,  # hardcoded to 1 to use only one tesseract thread pool
            log_level="info",
            **uvicorn_kwargs
        )
    else:
        logging.basicConfig(level=logging.DEBUG)
        uvicorn.run(
            app_name,
            reload=True,
            reload_excludes=list(get_reload_excludes()),
            log_level="debug",
            **uvicorn_kwargs
        )


def run(app_name):
    args = parse_args(app_name)
    run_uvicorn(app_name, args)


if __name__ == "__main__":
    run("tesseract_server.app:app")
