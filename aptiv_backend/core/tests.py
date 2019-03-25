# Create your tests here.
from .tasks import add
from time import sleep
from django import db

def TestCelery():
    mytask = add.apply_async(args=[3, 5])
    print(mytask.state)
    # assert mytask.state == 'PENDING', 'Celery not initiated'
    sleep(3)
    assert mytask.state == 'SUCCESS', 'State wrong: ' + mytask.state + '  (Are celery workers running?)'
    assert mytask.get() == 8, 'Wrong Result'
    print('TEST CELERY => OK')

# def TestDatabaseIsLocal():
#     mydbsettings = db.connections.databases['default']
#     assert mydbsettings['HOST'] == 'localhost', 'Host should be local - ' + mydbsettings['HOST']
#     print('TEST DATABASE => OK')
