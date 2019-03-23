import os
import subprocess

from .base import BASE_DIR


def load_sql(tables):
    print()

    for table in tables:
        filename = BASE_DIR + "/data/" + table.lower() + ".sql.bz2"
        if not os.path.exists(filename):
            print(filename, "missing")
            return False

    for table in tables:
        print("Load ", table)
        filename = BASE_DIR + "/data/" + table.lower() + ".sql.bz2"
        # small hack to load pg_dump directly
        ps = subprocess.Popen(("bzcat", filename),
                              stdout=subprocess.PIPE)
        output = subprocess.check_output(('python', 'manage.py',
                                          'dbshell'),
                                         stdin=ps.stdout)
        ps.wait()
        print(output)
    return True
