import logging
import time
import os
import shutil
from bson import objectid

import yamajudge
from yamajudge.util import options

options.define('run_dir', default='run', help='Record work directory.')
_logger = logging.getLogger(__name__)


class WorkSpace(object):

    def __init__(self, rid: objectid.ObjectId):
        self.rid = str(rid)
        self.main_folder = os.path.dirname(os.path.dirname(yamajudge.__file__))
        self.dump_folder = os.path.join(self.main_folder, 'dumps')
        self.run_folder = os.path.join(self.main_folder, options.options.run_dir)
        try:
            os.mkdir(self.run_folder)
        except FileExistsError:
            pass
        self.path = os.path.join(self.run_folder, self.rid)

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

    def dump(self):
        try:
            os.mkdir(self.dump_folder)
        except FileExistsError:
            pass
        dump_path = 'dump_{0}_{1}'.format(time.strftime('%Y%m%d_%H%M%S'), self.rid)
        dump_path = os.path.join(self.dump_folder, dump_path)
        try:
            shutil.move(self.path, dump_path)
        except Exception as e:
            raise e
