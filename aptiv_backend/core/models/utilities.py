import tabula, PyPDF2, re, os, xlrd

# Utility PDF fucntions
# checks at which column starts the partnumbers
def check_start_column(dataframe):
    aux = False
    col = -1
    while not aux:
        col += 1
        if not type(dataframe[col][0]) == float:
            if not re.match('\d{5,}', dataframe[col][0]):  # cell has to have 5 or more digits
                aux = True
    return col

def add_PartnumberToDictionary(partnumber, description, dictionary):
    added = True
    if partnumber in dictionary:
        dictionary[partnumber]["qty"] += 1
        if dictionary[partnumber]["description"] != description:
            added = False

    else:
        dictionary[partnumber] = {"qty": 1, "description": description}
    return added

# Parsing Methods
def pdf_to_tb(path, page):
    dt = tabula.read_pdf(path, output_format="dataframe", encoding="utf-8", java_options=None, pandas_options=None,
                         multiple_tables=True, pages=page)
    return dt  # returns list of the multiple dataframes inside a page
def pdf_to_tb_area(path, page, xl, yl, xr, yr):  # returns list of dataframes for a specific area
    df = tabula.read_pdf(path, output_format="dataframe", encoding="utf-8", java_options=None, pandas_options=None,
                         multiple_tables=True, pages=page, spreadsheet=True, area=(xl, yl, xr, yr))
    return df
# End Parsing Methods

# Uitliy Functions for Excel processing
def get_sheet(name, path):
    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_name(name)
    return sheet


def addAssembly(mount, assembly, item_name, dict):
    if mount in dict:
        dict[mount][assembly] = item_name
    else:
        dict[mount] ={}
        dict[mount][assembly] = item_name

def addWeight(mount, weight, dict):
    if mount in dict:
        if dict[mount]:
            dict[mount] += int(weight)
        else:
            dict[mount] = int(weight)

def get_StartRow(sheet, AssemblyRow, lenth_sheet):
    startRow = 0
    for row in range(AssemblyRow, lenth_sheet):
        if sheet.cell(row, 0).value == "Ll":
            startRow = row + 1
            break
    return startRow
# End of utility fucntions


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
