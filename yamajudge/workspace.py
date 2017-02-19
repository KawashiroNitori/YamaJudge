import logging
import os
import shutil
from bson import objectid

import yamajudge
from yamajudge.util import options

options.define('run_dir', default='run', help='Record work directory.')
_logger = logging.getLogger(__name__)


class WorkSpace(object):

    def __init__(self, rid: objectid.ObjectId):
        main_folder = os.path.dirname(os.path.dirname(yamajudge.__file__))
        run_folder = os.path.join(main_folder, options.options.run_dir)
        try:
            os.mkdir(run_folder)
        except FileExistsError:
            pass
        self.path = os.path.join(run_folder, str(rid))

    def __str__(self):
        return self.path

    __repr__ = __str__

    def __enter__(self):
        try:
            self.clean()
            os.mkdir(self.path)
            os.chmod(self.path, 0o777)
        except Exception as e:
            raise e
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.clean()
        except Exception as e:
            raise e

    def clean(self):
        try:
            shutil.rmtree(self.path)
        except FileNotFoundError:
            pass
        except Exception as e:
            raise e

    def join(self, *args):
        return os.path.join(self.path, *args)
