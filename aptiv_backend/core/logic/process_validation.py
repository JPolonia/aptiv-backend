# Uitlity functions for comparison
def check_Partnumbers(dictPDF_Partnumbers, dictPDF_OptPartnumbers,  dictExcel_Partnumbers):
    errorList = []
    for mount in dictPDF_Partnumbers:
        for assembly in dictPDF_Partnumbers[mount]:
            for partnumber in dictPDF_Partnumbers[mount][assembly]:
                if existsInDictionary(partnumber, assembly, mount, dictExcel_Partnumbers): #cheks if it exists in excel

                    # Checking Desctiprtion
                    descriptionPDF = dictPDF_Partnumbers[mount][assembly][partnumber]["description"]
                    descriptionExcel = dictExcel_Partnumbers[mount][assembly][partnumber]["description"]
                    if descriptionPDF != descriptionExcel:
                        error = "WARNING: Description of partnumber " + partnumber + " in assembly " + assembly + " " \
                                + mount + " does not match between PDF and Excel"
                        errorList.append(error)
                    # End of Checking description


                    # Checking Quantity
                    qtyPDF = int(dictPDF_Partnumbers[mount][assembly][partnumber]["qty"])
                    qtyExcel = int(dictExcel_Partnumbers[mount][assembly][partnumber]["qty"])
                    if qtyPDF > qtyExcel:
                        error = errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF)
                        errorList.append(error)
                    elif qtyPDF < qtyExcel:
                        # comparing optionals
                        qtyPDF = (dictPDF_Partnumbers[mount][assembly][partnumber]["qty"])
                        qtyExcel = (dictExcel_Partnumbers[mount][assembly][partnumber]["qty"])
                        qtyOPT = (dictPDF_OptPartnumbers[mount][assembly][partnumber]["qty"])
                        if not existsInDictionary(partnumber, assembly, mount, dictPDF_OptPartnumbers):
                            error = errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF)
                            errorList.append(error)
                        else:
                            qty_OPTplusInserted = qtyPDF + qtyOPT
                            if qtyExcel > qty_OPTplusInserted:  # checks if qty in excel is higher than the sum of mandatory partnumbers and optional
                                error = errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF)
                                errorList.append(error)
                    # End of Checking Quantity


                    del dictExcel_Partnumbers[mount][assembly][partnumber]
                else:
                    error = "ERROR: Partnumber " + partnumber + " does not exist in assembly " + assembly + " " + mount + " in Excel"
                    errorList.append(error)
                    #error(error)
    return errorList


def errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF):
    error = "ERROR: Quantity of partnumber " + partnumber + " in assembly " + assembly + " " + mount + " in Excel: "\
            +  str(qtyExcel) + " different from quantity in PDF: " + str(qtyPDF)
    return error

def existsInDictionary(partnumber, assembly, mount, dictionary):
    aux = False
    if mount in dictionary:
        if assembly in dictionary[mount]:
            if partnumber in dictionary[mount][assembly]:
                aux = True
    return aux
# End of utilty functions dor comparison

def processValidation(InfoPDF, InfoExcel):  # Pdf has 4 dict and excel has 2

    # InfoPDF = self.pdf.compare_json
    # InfoExcel = self.excel.compare_json

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

    print('\n'.join(errorList))

    return '\n'.join(errorList)
