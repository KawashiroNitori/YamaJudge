from yamajudge.constant import record


def judge(user_out: str, correct_out: str, ignore_space=True):
    if ignore_space:
        correct_out = correct_out.rstrip()
        user_out = user_out.rstrip()

    ans_list = [correct_out.split('\n'), user_out.split('\n')]

    if len(ans_list[0]) != len(ans_list[1]):
        return record.STATUS_WRONG_ANSWER, \
               'Lines mismatch: %d except %d.' % (len(ans_list[0]), len(ans_list[1]))

    if ignore_space:
        ans_list[0] = list(map(lambda s: s.rstrip(), ans_list[0]))
        ans_list[1] = list(map(lambda s: s.rstrip(), ans_list[1]))

    for i in range(len(ans_list[0])):
        if ans_list[0][i] != ans_list[1][i]:
            return record.STATUS_WRONG_ANSWER, \
                   'Mismatch (%d): \'%s\' except \'%s\'.' % (i + 1, ans_list[0][i], ans_list[1][i])

    return record.STATUS_ACCEPTED, 'Well done!'
