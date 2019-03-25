from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def aptiv_validate(request):

    filesList = []
    if request.method == 'POST' and request.FILES['input2']:
        files = request.FILES.getlist('input2')

        for file in files:

            filesList.append(file.name)
            print(file)

            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            uploaded_file_url = fs.url(filename)

            # if file.name.endswith('.pdf'):
            #     pdf = "files/" + fname

        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)

        return render(request, 'core/aptiv_validate.html', {
            'uploaded_file_url': uploaded_file_url
        })

    return render(request, 'core/aptiv_validate.html')
