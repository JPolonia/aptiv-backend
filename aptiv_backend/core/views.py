from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def aptiv_validate(request):
    if request.method == 'GET':
        # myfile = request.FILES['myfile']
        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)
        return render(request, 'core/aptiv_validate.html', {
            'uploaded_file_url': 'OK'
        })
    return render(request, 'core/aptiv_validate.html')
