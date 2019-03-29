from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .models import Pdf, Excel, AptivValidate

def aptiv_validate(request):

    filesList = []
    if request.method == 'POST' and request.FILES['documentPDF'] and request.FILES['documentExcel']:

        pdf_file = request.FILES['documentPDF']
        excel_file = request.FILES['documentExcel']

        excel = Excel(excel_file=excel_file)
        excel.save()

        pdf = Pdf(pdf_file=pdf_file)
        pdf.save()

        validation = AptivValidate(pdf=pdf, excel=excel)
        validation.save()

        # files = request.FILES.getlist('input2')
        #
        # for file in files:
        #
        #     filesList.append(file.name)
        #     print(file)
        #
        #     fs = FileSystemStorage()
        #     filename = fs.save(file.name, file)
        #     uploaded_file_url = fs.url(filename)

            # if file.name.endswith('.pdf'):
            #     pdf = "files/" + fname

        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)

        return render(request, 'core/aptiv_validate.html', {
            'output': validation.output
        })

    return render(request, 'core/aptiv_validate.html')
