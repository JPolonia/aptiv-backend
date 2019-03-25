from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from .utilities import check_Partnumbers
from .pdf import Pdf
from .excel import Excel


def output_file_path(instance, filename):
    return settings.OUTPUT_PATH + filename

class AptivValidate(models.Model):
    pdf = models.ForeignKey(Pdf, blank= True, null= True, on_delete=models.CASCADE, verbose_name='PDF')
    excel = models.ForeignKey(Excel, blank=True, null=True, on_delete=models.CASCADE, verbose_name='EXCEL')

    output = models.TextField(_('OUTPUT'), null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def save(self,update=True, new=False, *args, **kwargs):
        if self.id is None:
            new = True

        super(AptivValidate, self).save(*args, **kwargs)

        if new or update:
            self.compare()

    def compare(self):  # Pdf has 4 dict and excel has 2

        InfoPDF = self.pdf.compare_json
        InfoExcel = self.excel.compare_json

        dictionaryPDF = InfoPDF
        dictionaryExcel = InfoExcel

        dictPDF_Components = dictionaryPDF["Components"]
        dictPDF_OptComponents = dictionaryPDF["OptionalComponents"]
        dictPDF_AdditionalFeatures = dictionaryPDF["AdditionalFeatures"]
        dictPDF_OptAdditionalFeatures = dictionaryPDF["OptionalAdditionalFeatures"]
        dictExcel_Components = dictionaryExcel["Components"]
        dictExcel_AdditionalFeatures = dictionaryExcel["AdditionalFeatures"]
        error_list1 = check_Partnumbers(dictPDF_Components, dictPDF_OptComponents,
                                        dictExcel_Components)  # validation of inserted components
        error_list2 = check_Partnumbers(dictPDF_AdditionalFeatures, dictPDF_OptAdditionalFeatures,
                                        dictExcel_AdditionalFeatures)  # validation of inserted addtional features

        errorList = error_list1
        for error in range(len(error_list2)):
            errorList.append(error_list2[error])

        self.output = '\n'.join(errorList)
        print(self.output)
        self.save(update=False)




