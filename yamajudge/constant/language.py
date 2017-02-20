lang_config = {
    'c': {
        'src_name': 'Main.c',
        'exe_name': 'Main',
        'time_rate': 1.0,
        'compile_command': '/usr/bin/gcc --static -DONLINE_JUDGE -O2 -Wall -fno-asm -std=c99 Main.c -lm -o Main',
        'run_command': './Main',
        'seccomp_rule': 'c_cpp',
    },
    'cc': {
        'src_name': 'Main.cc',
        'exe_name': 'Main',
        'time_rate': 1.0,
        'compile_command': '/usr/bin/g++ --static -DONLINE_JUDGE -O2 -Wall -fno-asm -std=c++11 Main.cc -lm -o Main',
        'run_command': './Main',
        'seccomp_rule': 'c_cpp',
    },
    'java': {
        'src_name': 'Main.java',
        'exe_name': 'Main',
        'time_rate': 3.0,
        'compile_command': '/usr/bin/javac Main.java',
        'run_command': '/usr/bin/java -Xss1M \
                        -Xms16M -Xmx{memory_kb}k -Djava.security.policy==java_policy \
                        -Djava.awt.headless=true Main',
        'seccomp_rule': None,
    }
}
