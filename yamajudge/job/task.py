import logging
import os
import shutil
import pwd
import grp
from bson import objectid

import _judger

import yamajudge
from yamajudge import db
from yamajudge import request
from yamajudge import error
from yamajudge import workspace
from yamajudge import judge
from yamajudge.constant import record
from yamajudge.constant import language

_logger = logging.getLogger(__name__)


class JudgeTask(object):
    def __init__(self, rid: objectid.ObjectId):
        self.rid = rid
        try:
            rdoc, pdoc, ddoc = self.fetch_data()
        except error.Error as e:
            raise e

        self.code = rdoc['code']
        self.lang = rdoc['lang']
        self.time_ms = pdoc['time_ms']
        self.memory_kb = pdoc['memory_kb']
        self.data = ddoc['data']
        self.judge_mode = pdoc.get('judge_mode', record.MODE_COMPARE_IGNORE_SPACE)
        self.config = language.lang_config[rdoc['lang']]

    def fetch_data(self):
        record_coll = db.Collection('record')
        problem_coll = db.Collection('problem')
        data_coll = db.Collection('testdata')

        # Get record doc.
        rdoc = record_coll.find_one({'_id': self.rid})
        if not rdoc:
            raise error.RecordNotFoundError(self.rid)
        # Get problem doc.
        pdoc = problem_coll.find_one({'_id': rdoc['pid']})
        if not pdoc:
            raise error.ProblemNotFoundError(rdoc['pid'])
        if rdoc['data_id']:
            data_id = rdoc['data_id']
        else:
            data_id = pdoc['data']
        # Get data.
        ddoc = data_coll.find_one({'_id': data_id})
        if not ddoc:
            raise error.TestDataNotFoundError(data_id)
        return rdoc, pdoc, ddoc

    def prepare_file(self, work_dir):
        with open(work_dir.join(self.config['src_name']), 'w') as file:
            file.write(self.code)
        shutil.copy(os.path.join(os.path.dirname(os.path.dirname(yamajudge.__file__)),
                                 'java_policy'), work_dir)

    def compile(self, work_dir):
        command = self.config['compile_command'].split(' ')
        compile_out = work_dir.join('compile.out')
        result = _judger.run(max_cpu_time=10000,
                             max_real_time=10000,
                             max_memory=_judger.UNLIMITED,
                             max_output_size=_judger.UNLIMITED,
                             exe_path=command[0],
                             input_path=work_dir.join(self.config['src_name']),
                             output_path=compile_out,
                             error_path=compile_out,
                             args=command[1:],
                             env=['PATH=' + os.getenv('PATH')],
                             log_path=work_dir.join('compile.log'),
                             seccomp_rule_name=None,
                             uid=pwd.getpwnam('judger').pw_uid,
                             gid=grp.getgrnam('judger').gr_gid)

        compiler_text = ''
        if os.path.exists(compile_out):
            with open(compile_out) as file:
                compiler_text = file.read().strip()
        return result['result'], compiler_text

    def execute(self, work_dir, input_str):
        in_file = work_dir.join('in_file')
        out_file = work_dir.join('out_file')
        log_file = work_dir.join('runner.out')
        command = self.config['run_command'].format(memory_kb=self.memory_kb).split(' ')
        with open(in_file, 'w') as file:
            file.write(input_str)
        result = _judger.run(max_cpu_time=self.time_ms,
                             max_real_time=self.time_ms * 5,
                             max_memory=self.memory_kb * 1024 if self.lang != 'java' else _judger.UNLIMITED,
                             max_output_size=4 * 1024 * 1024,   # 4MiB
                             max_process_number=_judger.UNLIMITED,
                             exe_path=command[0],
                             input_path=in_file,
                             output_path=out_file,
                             error_path=out_file,
                             args=command[1:],
                             env=['PATH=' + os.getenv('PATH')],
                             log_path=log_file,
                             seccomp_rule_name=self.config['seccomp_rule'],
                             uid=pwd.getpwnam('nobody').pw_uid,
                             gid=grp.getgrnam('nogroup').pw_gid)

        out_ans = ''
        if result['result'] == _judger.RESULT_SUCCESS:
            with open(out_file) as file:
                out_ans = file.read()
        result['memory'] //= 1024
        return result, out_ans

    def judge(self, user_out, correct_out):
        # TODO: add special judge.
        if self.judge_mode == record.MODE_COMPARE_IGNORE_SPACE:
            return judge.judge(user_out, correct_out, ignore_space=True)
        else:
            return judge.judge(user_out, correct_out, ignore_space=False)

    def next_judge(self, **kwargs):
        request.next_judge(self.rid, **kwargs)

    def end_judge(self, status: int, time_ms: int=0, memory_kb: int=0):
        request.end_judge(self.rid, status, time_ms, memory_kb)

    def run(self):
        with workspace.WorkSpace(self.rid) as work_dir:
            os.chdir(work_dir)
            self.prepare_file(work_dir)
            compile_result, compiler_text = self.compile(work_dir)
            self.next_judge(compiler_text=compiler_text)
            if compile_result != _judger.RESULT_SUCCESS:  # Compile Error
                self.end_judge(record.STATUS_COMPILE_ERROR)
                return
            # Execute your program
            total_time_ms = 0
            max_memory = 0
            final_result = record.STATUS_ACCEPTED
            self.next_judge(status=record.STATUS_JUDGING, progress=0.0)

            for index, case in enumerate(self.data, start=1):
                result, user_out = self.execute(work_dir, case[0])
                judge_text = ''
                if result['result'] == _judger.RESULT_SUCCESS:
                    # Have to judge
                    result['result'], judge_text = self.judge(user_out, case[1])

                # Update record information.
                total_time_ms += result['cpu_time']
                max_memory = max(max_memory, result['memory'])
                final_result = max(final_result, result['result'])
                self.next_judge(progress=index / len(self.data),
                                case=True,
                                case_status=result['result'],
                                case_time_ms=result['cpu_time'],
                                case_memory_kb=result['memory'],
                                case_judge_text=judge_text)
                if result['result'] == record.STATUS_SYSTEM_ERROR or \
                        result['result'] == record.STATUS_TIME_LIMIT_EXCEEDED:
                    # TLE or SE will stop judge immediately
                    self.end_judge(status=result['result'],
                                   time_ms=total_time_ms,
                                   memory_kb=max_memory)
                    return

            self.end_judge(status=final_result, time_ms=total_time_ms, memory_kb=max_memory)