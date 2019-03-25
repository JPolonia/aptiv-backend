from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings

from .utilities import pdf_to_tb, pdf_to_tb_area, check_start_column, add_PartnumberToDictionary

import tabula, PyPDF2,xlrd
import re,os,json, tempfile

def import_file_path(instance, filename):
    return settings.UPLOAD_PATH + filename


class Pdf(models.Model):
    pdf_file = models.FileField(upload_to=import_file_path)
    # pdf_rotated = models.FileField(upload_to=import_file_path)

    num_pages = models.IntegerField(null=True, blank=True)

    rev_letter = models.CharField(max_length=10, null=True, blank=True, default=None)
    compare_id = models.CharField(max_length=20, null=True, blank=True)

    compare_json = JSONField(null=True, blank=True)

    error_msg = models.TextField(null=True, blank=True)


    def save(self, *args, **kwargs):
        new = False

        if self.id is None:
            new = True

        super(Pdf, self).save(*args, **kwargs)

        if new:
            self.processPDF()





    def processPDF(self):

        # if(self):
        pathPDF = self.pdf_file.path
        # rev_letter = ""
        # num_pages = 0
        # compare_id = 0
        # compare_json = ""

        errorList = []

        # gets number of pages id the PDF file
        pdf_file = open(pathPDF, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        num_pages = PyPDF2.PdfFileReader.getNumPages(pdf_reader)

        # Validating Pages
        # Parses PDF to python and returns list of pages that exclude ignorable ones (marked has "ignore")
        pages = []
        pages.append(pdf_to_tb(pathPDF, 1))
        pages[0].append(pdf_to_tb_area(pathPDF, 1, 73.01, 1743.3, 1682.21, 2363.14))  # retrieves date table info
        for pageNumber in range(2, num_pages + 1):
            page = pdf_to_tb_area(pathPDF, pageNumber, 34.27, 32.78, 1649.43,
                                  2360.16)  # only retrieve info thats inside the outer grid
            # Page Validation
            aux = False
            for pageNumb in range(0, len(page) - 1):
                if page[pageNumb][0][
                    0] == "If Package name is not available, then up to 15 characters of the geometry name\rwill appear in parentheses":
                    aux = True
                    break
            if not aux:  # unuseful pages are marked as ignore
                page = "ignore"
            # End of Page Validation
            pages.append(page)
        # Ignore CMP
        pageNumber = num_pages
        aux = False
        while not aux and pageNumber > -1:  # assuming that CMP page is either last page or is only before ignorable pages
            if pages[pageNumber - 1] == "ignore":
                pageNumber = pageNumber - 1
            else:
                pages[pageNumber - 1] = "ignore"
                aux = True
        # End of ignoring CMP
        # End of page validation

        # Retrieving Revision Letter
        page = pages[0]
        rev = ""
        row = 0
        while row <= len(page[5][0][2]):
            rev = page[5][0][2][row]
            aux = True
            for i in range(row + 1, row + 6):
                if not type(page[5][0][2][i]) == float:
                    aux = False
            if aux:
                if not type(rev) == float:
                    row = len(page[5][0][2])
            row += 1
        rev_letter = rev
        # End of Retrieving Revision Letter

        # Retrieve number ID - number of pdf to check if excel corresponds
        page = pages[0]
        row = 0
        while True:
            if page[5][0][2][row] == rev_letter:
                break
            else:
                row += 1

        compare_id = page[5][0][7][row]
        compare_id.replace(" ", "")
        # End of retrieving ID

        # Method for Checking Revision for Errors
        page = pages[0]
        dataframe = page[3]
        startColumn = check_start_column(dataframe)
        list_Finders = []
        list_Revisions = []

        for row in range(len(dataframe[0]) - 1, -1, -1):
            if type(dataframe[startColumn][row]) != float:
                if "." in dataframe[startColumn][row]:
                    revLetter = dataframe[startColumn + 3][row]
                    list_Revisions.append(revLetter)
                    list_Finders.append(list_Revisions)
                    list_Revisions.reverse()
                    list_Revisions = []
                else:
                    revLetter = dataframe[startColumn + 3][row]
                    list_Revisions.append(revLetter)
        list_Finders.reverse()

        for finder in range(len(list_Finders)):
            counter = 0
            last_Rev = list_Finders[finder][0]
            for revision in range(1, len(list_Finders[finder])):
                revLetter = list_Finders[finder][revision]
                if revLetter == last_Rev:
                    counter += 1
                elif revLetter >= last_Rev:
                    error = "Error: Assembly in position " + str(
                        revision + 1) + " has later revision than CMP in finder " + str(finder + 1)
                    errorList.append(error)
            if counter == 0:
                warning = "Warning: CMP has later revision than all assemblies in finder " + str(finder + 1)
                errorList.append(warning)
        # End of Method for Checking Revision for Errors

        # Getting a list of mounts that appear in 1st page
        MountList = []
        # Checking which Mounts appear in 1st page table
        dataframe = pages[0][3]  # page 0 is the first one, and the info is in dataframe number 3, always
        start_column = check_start_column(dataframe)
        existsSM1 = False
        existsSM2 = False
        existsHP1 = False
        for col in range(len(dataframe[0])):
            if not type(dataframe[start_column + 1][col]) == float:
                if "SM1" in dataframe[start_column + 1][col]:
                    existsSM1 = True
                elif "SM2" in dataframe[start_column + 1][col]:
                    existsSM2 = True
                elif "HP1" in dataframe[start_column + 1][col]:
                    existsHP1 = True
        # End of Checking which Mounts appear in 1st page table
        # Adding Mounts to list:
        if existsSM1:
            MountList.append("SM1")
        if existsSM2:
            MountList.append("SM2")
        if existsHP1:
            MountList.append("HP1")
        # End of Getting a list of mounts that appear in 1st page

        # Retrieving dictPagesPerMount
        # Getting Data List with blocks of pages that will correspond to a mount from MountList
        DataList = []
        nPage = len(pages)
        pageIndex = nPage - 1
        aux = False
        # while starts at end of pdf file
        while pageIndex > 1:  # the identfying element that tels us wchic pages separate mounts is "ignore"
            if pages[pageIndex] == "ignore":
                if not pageIndex == nPage - 1:  # if page is not last one
                    # checks if previous page was ignore, because there's only 1 ignore between mounts
                    if not pages[pageIndex + 1] == "ignore":
                        array = []
                        x = pageIndex + 1
                        while pages[x] != "ignore":  # gets all pages until it finds an "ignore"
                            array.append(pages[x])
                            x += 1
                        DataList.append(array)
            pageIndex = pageIndex - 1
        DataList.reverse()
        # End of Getting Data List with blocks of pages that will correspond to a mount from MountList

        # Associating both lists
        dictPagesPerMount = {}
        for i in range(len(DataList)):
            dictPagesPerMount[MountList[i]] = DataList[i]
        if not len(DataList) == len(MountList):
            error = "ERROR: Not every mount from 1st page is defined through out PDF or otherwise, rest of analysis might be corrupted"
            errorList.append(error)
        # End of Associating both lists
        # End of Retrieving dictPagesPerMount

        # Retrieving dictVerticalAssembly - Aggreggate the vertical assemblies arrays in a dictionary


        # Rotate PDF 90º
        pdf_in = open(pathPDF, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_in)
        pdf_writer = PyPDF2.PdfFileWriter()

        for pageNumb in range(pdf_reader.numPages):
            page = pdf_reader.getPage(pageNumb)
            page.rotateClockwise(90)
            pdf_writer.addPage(page)


        print(settings.MEDIA_ROOT)

        path_out = settings.MEDIA_ROOT + '/' + settings.UPLOAD_PATH + 'rotated.pdf'

        pdf_out = open(path_out, 'wb')
        pdf_writer.write(pdf_out)
        pdf_out.close()
        pdf_in.close()
        # End of Rotate PDF 90º

        listCheckedAssembly = []
        for pagenum in range(len(pages) - 1, 1, -1):
            if pages[pagenum] == "ignore":
                if not pages[pagenum - 1] == "ignore":

                    # Retrive Data from rotated file
                    page = pdf_to_tb_area(path_out, pagenum, 28.418, 1444.03, 2352.338,
                                          1652.425)  # retrieves by area
                    assemblyArray = []  # gets an array of assemblies that will correspond to a mount
                    aux = True
                    i = 0
                    while aux:
                        assemblyArray.append(page[0][0][i])
                        number = page[0][0][i + 1]
                        if not type(number) == float:  # drop all float values… … but only if they are nan
                            if not re.match('\d{5,}',
                                            number):  # checks if string has 5 digits or more, if not it ends the cycle
                                aux = False
                        else:
                            aux = False
                        i += 1
                    # End of Retrieving Data from rotated file

                    listCheckedAssembly.append(assemblyArray)

        listCheckedAssembly.reverse()
        if os.path.exists(path_out):
            print(path_out)
            os.remove(path_out)
        else:
            print("The file does not exist")
        # os.remove(path_out)

        dictVerticalAssembly = {}
        for mount in range(len(MountList)):
            dictVerticalAssembly[MountList[mount]] = {}
        for i in range(len(listCheckedAssembly)):
            dictVerticalAssembly[MountList[i]] = listCheckedAssembly[i]
        if not len(listCheckedAssembly) == len(MountList):
            error = "Not every mount from 1st page is defined through out PDF or otherwise, rest of analysis might be corrupted"
            errorList.append(error)
        # End of Retrieving dictVerticalAssembly

        # Building the final dictionaries
        dictComponents = {}
        dictOptionalComponents = {}
        dictAdditionalFeatures = {}
        dictOptionalAdditionalFeatures = {}

        # Adding to respective mounts, the assemblies that are signelized as being last revised.
        dataframe = pages[0][3]
        revAssemblyList = {"SM1": [], "SM2": [], "HP1": []}
        start_column = check_start_column(dataframe)
        # Get row of revised assemblies
        column = start_column + 3
        positionsList = []
        for row in range(len(dataframe[column])):
            if dataframe[column][row] == rev_letter:
                positionsList.append(row)
        # End of Get postions of revised assemblies

        # Build list of assemblies that are revised
        for value in positionsList:
            if "SM1" in dataframe[start_column + 1][value]:
                revAssemblyList["SM1"].append(dataframe[start_column][value])
                sorted(revAssemblyList["SM1"])
            elif "SM2" in dataframe[start_column + 1][value]:
                revAssemblyList["SM2"].append(dataframe[start_column][value])
                sorted(revAssemblyList["SM2"])
            elif "HP1" in dataframe[start_column + 1][value]:
                revAssemblyList["HP1"].append(dataframe[start_column][value])
                sorted(revAssemblyList["HP1"])
        # Enf of Adding to respective mounts, the assemblies that are signelized as being last revised.

        positionsDict = {}
        for mount in MountList:
            positionsDict[mount] = {}

        total_columns = {}
        for mount in dictVerticalAssembly:
            total_columns[mount] = len(dictVerticalAssembly[mount])

        for mount in revAssemblyList:
            if revAssemblyList[mount] is not None:
                if mount in dictVerticalAssembly:
                    for i in range(total_columns[mount]):
                        if dictVerticalAssembly[mount][i] in revAssemblyList[mount]:
                            positionsDict[mount][dictVerticalAssembly[mount][i]] = i

        for mount in revAssemblyList:
            if revAssemblyList[mount] != []:
                dictComponents[mount] = {}
                dictOptionalComponents[mount] = {}
                dictAdditionalFeatures[mount] = {}
                dictOptionalAdditionalFeatures[mount] = {}
                for assembly in range(len(revAssemblyList[mount])):
                    dictComponents[mount][revAssemblyList[mount][assembly]] = {}
                    dictOptionalComponents[mount][revAssemblyList[mount][assembly]] = {}
                    dictAdditionalFeatures[mount][revAssemblyList[mount][assembly]] = {}
                    dictOptionalAdditionalFeatures[mount][revAssemblyList[mount][assembly]] = {}
                    for page in range(len(dictPagesPerMount[mount])):
                        for table in range(len(dictPagesPerMount[mount][page])):

                            # Checking if dataframe is the one we are looking for
                            dataframe = dictPagesPerMount[mount][page][table]
                            checkDataframe = False
                            x = len(dataframe.columns)
                            y = start_column
                            if len(dataframe.columns) - len(
                                dictVerticalAssembly[mount]) == 4:  # no of non assembly columns  is 4
                                checkDataframe = True
                            # End of Checking if dataframe is the one we are looking for

                            if checkDataframe:
                                dataframe = dictPagesPerMount[mount][page][table]

                                col = positionsDict[mount][revAssemblyList[mount][assembly]]
                                nColumns_toCheck = len(dictVerticalAssembly[mount])
                                partnumbers = {}
                                optional_partnumbers = {}
                                additionalFeatures = {}
                                optional_additionalFeatures = {}
                                error = "nothing"

                                for row in range(len(dataframe[0])):
                                    if type(dataframe[0][row]) == float:
                                        if type(dataframe[0][row + 1]) != float:
                                            row = row + 1
                                            break
                                start_row = row

                                for row in range(start_row, len(dataframe[0])):
                                    added = True
                                    if dataframe[col][row] == "1":
                                        partnumber = dataframe[nColumns_toCheck + 1][row]
                                        description = dataframe[nColumns_toCheck + 2][row]
                                        if "MA" in partnumber:  # checks if is an additional feauture
                                            added = add_PartnumberToDictionary(partnumber, description,
                                                                               additionalFeatures)
                                        elif not "LOCAL_FID" in partnumber and not "GLOBAL_FID" in partnumber:
                                            added = add_PartnumberToDictionary(partnumber, description,
                                                                               partnumbers)

                                        if not added:
                                            error = "Warning: Component: ", partnumber, "has different descriptions"
                                            errorList.append(error)
                                    elif dataframe[col][row] == "O01":
                                        partnumber = dataframe[nColumns_toCheck + 1][row]
                                        description = dataframe[nColumns_toCheck + 2][row]
                                        if "MA" in partnumber:  # checks if is an additional feauture
                                            added = add_PartnumberToDictionary(partnumber, description,
                                                                               optional_additionalFeatures)
                                        elif not "LOCAL_FID" in partnumber and not "GLOBAL_FID" in partnumber:
                                            added = add_PartnumberToDictionary(partnumber, description,
                                                                               optional_partnumbers)
                                        if not added:
                                            error = "Warning: Component: ", partnumber, "has different descriptions"
                                            errorList.append(error)

                                for value in partnumbers:
                                    if not value in dictComponents[mount][revAssemblyList[mount][assembly]]:
                                        dictComponents[mount][revAssemblyList[mount][assembly]][value] = partnumbers[
                                            value]
                                    else:
                                        dictComponents[mount][revAssemblyList[mount][assembly]][value]["qty"] += \
                                            partnumbers[value]["qty"]
                                for value in optional_partnumbers:
                                    if not value in dictOptionalComponents[mount][revAssemblyList[mount][assembly]]:
                                        dictOptionalComponents[mount][revAssemblyList[mount][assembly]][value] = \
                                            optional_partnumbers[value]
                                    else:
                                        dictOptionalComponents[mount][revAssemblyList[mount][assembly]][value]["qty"] += \
                                            optional_partnumbers[value]["qty"]
                                for value in additionalFeatures:
                                    if not value in dictAdditionalFeatures[mount][revAssemblyList[mount][assembly]]:
                                        dictAdditionalFeatures[mount][revAssemblyList[mount][assembly]][value] = \
                                            additionalFeatures[value]
                                    else:
                                        dictAdditionalFeatures[mount][revAssemblyList[mount][assembly]][value][
                                            "qty"] += additionalFeatures[value]["qty"]

                                for value in optional_additionalFeatures:
                                    if not value in dictOptionalAdditionalFeatures[mount][
                                        revAssemblyList[mount][assembly]]:
                                        dictOptionalAdditionalFeatures[mount][revAssemblyList[mount][assembly]][value] = \
                                            optional_additionalFeatures[value]
                                    else:
                                        dictOptionalAdditionalFeatures[mount][revAssemblyList[mount][assembly]][value][
                                            "qty"] += optional_additionalFeatures[value]["qty"]
            # End of Building the final dictionary

        # Retreiveing a list of pdf dictionaries
        list_PDF = {}
        list_PDF["Components"] = dictComponents
        list_PDF["OptionalComponents"] = dictOptionalComponents
        list_PDF["AdditionalFeatures"] = dictAdditionalFeatures
        list_PDF["OptionalAdditionalFeatures"] = dictOptionalAdditionalFeatures
        # End of Retreiveing a list of pdf dictionaries

        # Writing dictionaries to json
        compare_json = json.dumps(list_PDF, indent=4, sort_keys=True)
        # compare_json = JSONField()
        # print(compare_json)
        print(list_PDF)
        # End of Writing dictionaries to json

        self.rev_letter = rev_letter
        self.num_pages = num_pages
        self.compare_id = compare_id
        self.compare_json = list_PDF
        self.error_msg = ''.join(errorList)
        self.save()







