import xlrd, re

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

def processExcel(path):
    # path = self.excel_file.path

    errorList = []

    sheet_EBOM_DATA = get_sheet("EBOM Data", path)
    sheet_IDM = get_sheet("ITEM MASTER Data", path)
    sheet_APPROVAL = get_sheet("APPROVAL", path)

    # Last rev letter and ID (CN number)
    rev_letter = sheet_APPROVAL.cell(4, 1).value
    compare_id = sheet_APPROVAL.cell(4, 3).value

    # Getting IMD assembly star row
    nRowsIDM = sheet_IDM.nrows
    startRowIDM = 0
    for row in range(nRowsIDM):
        if sheet_IDM.cell(row, 0) == "Name":
            startRowIDM = row + 1
        break
    # End of Getting IMD assembly star row

    # Getting assemblies that were revised/ mounts and weights
    weights = {}
    dict_RevAssemblies = {}
    for row in range(startRowIDM, nRowsIDM):
        name = sheet_IDM.cell(row, 0).value

        # Retrieving assembly number
        lenth_assembly = 0
        for chr in range(len(name)):
            if name[lenth_assembly] == ",":
                break
            else:
                lenth_assembly += 1
        assembly = name[:(lenth_assembly)]
        # End of Retrieving assembly number

        item_name = sheet_IDM.cell(row, 1).value
        weight = sheet_IDM.cell(row, 6).value
        if "SM1" in item_name:
            addAssembly("SM1", assembly, item_name, dict_RevAssemblies)
            addWeight("SM1", weight, weights)
        elif "SM2" in item_name:
            addAssembly("SM2", assembly, item_name, dict_RevAssemblies)
            addWeight("SM2", weight, weights)
        elif "HP1" in item_name:
            addAssembly("HP1", assembly, item_name, dict_RevAssemblies)
            addWeight("HP1", weight, weights)
        elif "CMP" in item_name:
            addAssembly("CMP", assembly, item_name, dict_RevAssemblies)
            addWeight("SM1", weight, weights)
    # Comparing weights
    if "CMP" in weights:
        for mount in weights:
            if mount != "CMP":
                if weights["CMP"] < weights[mount]:
                    error = "Error: CMP lighter than " + mount
                    errorList.append(error)
    if "HP1" in weights:
        aux = True
        for mount in weights:
            if mount != "CMP" and mount != "HP1":
                if weights["HP1"] < weights[mount]:
                    aux = False
        if not aux:
            error = "Error: HP1 not heavier than SM1 or SM2"
            errorList.append(error)
    if "SM2" in weights:
        for mount in weights:
            if mount != "SM1":
                if weights["SM1"] > weights[mount]:
                    error = "Error: SM1 heavier than " + mount
                    errorList.append(error)
    if "SM1" in weights:
        aux = True
        for mount in weights:
            if mount != "SM2" and mount != "SM1":
                if weights["SM2"] > weights[mount]:
                    aux = False
        if not aux:
            error = "Error: SM2 not lighter than HP1 or CMP"
            errorList.append(error)
    # End of Comparing weights
    # End of Getting assemblies that were revised/ mounts and weights

    # Getting DataList, containign all tables per each assembly/ mount
    list_Assemblies = []
    nRowsED = sheet_EBOM_DATA.nrows
    for row in range(nRowsED):
        if sheet_EBOM_DATA.cell(row, 0).value == "Part Number":
            list_Assemblies.append(
                [row, sheet_EBOM_DATA.cell(row, 1).value, sheet_EBOM_DATA.cell(row + 3, 1).value])
    # contains star row, assembly number and assembly description

    dict_DataList = {}
    for mount in dict_RevAssemblies:
        dict_DataList[mount] = {}

    # doesn't check last table
    for list_index in range(len(list_Assemblies) - 1):
        assembly = list_Assemblies[list_index][1]  # assembly number
        list_dataList = []
        assemblyRow = list_Assemblies[list_index][0]  # position 0 of array in list is the row number
        start_row = get_StartRow(sheet_EBOM_DATA, assemblyRow, nRowsED)
        end_row = list_Assemblies[list_index + 1][0] - 2  # table ends 3 rows above partnumber
        for row in range(start_row, end_row):
            lineData = sheet_EBOM_DATA.row_values(row, 1, 7)
            list_dataList.append(lineData)

        description = list_Assemblies[list_index][2]
        mount = ""
        if "SM1" in description:
            mount = "SM1"
        elif "SM2" in description:
            mount = "SM2"
        elif "HP1" in description:
            mount = "HP1"
        elif "CMP" in description:
            mount = "CMP"
        dict_DataList[mount][assembly] = list_dataList

    # last table
    assemblyRow = list_Assemblies[len(list_Assemblies) - 1][0]
    start_row = get_StartRow(sheet_EBOM_DATA, assemblyRow, nRowsED)
    end_row = sheet_EBOM_DATA.nrows
    assembly = list_Assemblies[len(list_Assemblies) - 1][1]
    list_dataList = []
    for row in range(start_row, end_row):
        lineData = sheet_EBOM_DATA.row_values(row, 1, 7)
        list_dataList.append(lineData)

    description = list_Assemblies[len(list_Assemblies) - 1][2]
    mount = ""
    if "SM1" in description:
        mount = "SM1"
    elif "SM2" in description:
        mount = "SM2"
    elif "HP1" in description:
        mount = "HP1"
    elif "CMP" in description:
        mount = "CMP"
    dict_DataList[mount][assembly] = list_dataList

    # Checking coherence bewtweeb IMD & EBData
    for mount in dict_RevAssemblies:
        for assembly in dict_RevAssemblies[mount]:
            if not assembly in dict_DataList[mount]:
                error = "Error:" + " assembly: " + str(assembly) + " , " + str(
                    mount) + " from ITEM MASTER Data is not present in " + str(mount) + " in EBOM Data"
                errorList.append(error)
    # End of Checking Coherence

    # Checking if CMP has the mandatory features EDD/ DWG/ Schematic
    if "CMP" in dict_DataList:
        for assembly in dict_DataList["CMP"]:
            edd = "EDD"
            dwg = "DWG"
            schematic = "SCHEMATIC"
            for part in range(len(dict_DataList["CMP"][assembly])):
                partnumber = dict_DataList["CMP"][assembly][part][1]
                description = dict_DataList["CMP"][assembly][part][3]
                if "EDD" in partnumber:
                    edd = ""
                elif "DWG" in partnumber:
                    dwg = ""
                elif "SCHEMATIC" in description:
                    schematic = ""
            if edd != "" or dwg != "" or schematic != "":
                error = "ERROR: " + "assembly: " + assembly + " => CMP is missing " + edd + " " + dwg + " " + schematic
                errorList.append(error)
    # End of Checking if CMP has the mandatory features EDD/ DWG/ Schematic

    # Building the Final Diciotnary
    dict_Partnumbers = {}
    dict_AdditionalFeatures = {}
    for mount in dict_DataList:
        dict_Partnumbers[mount] = {}
        dict_AdditionalFeatures[mount] = {}
        for assembly in dict_DataList[mount]:
            dict_Partnumbers[mount][assembly] = {}
            dict_AdditionalFeatures[mount][assembly] = {}
            table = dict_DataList[mount][assembly]

            # Getting Component Partnumbers and Addtionional Features
            partnumbers = {}
            additional_features = {}
            for item in range(len(table)):
                IsNumber = re.match('\d{1,}', table[item][0])  # check if there are digits in de F/N column
                if IsNumber:
                    number = table[item][1]
                    description = table[item][3]
                    if not table[item][5] == "PC":
                        additional_features[number] = {"qty": 1, "description": description}
                    else:
                        qty = table[item][4]
                        partnumbers[number] = {"qty": qty, "description": description}
            # End of Getting Component Partnumbers and Addtionional Features

            for value in partnumbers:
                if not value in dict_Partnumbers[mount][assembly]:
                    dict_Partnumbers[mount][assembly][value] = partnumbers[value]
                else:
                    error = "Partnumber is repeated in: " + assembly + " in " + mount
                    errorList.append(error)
            for value in additional_features:
                if not value in dict_AdditionalFeatures[mount][assembly]:
                    dict_AdditionalFeatures[mount][assembly][value] = additional_features[value]
                else:
                    error = "Partnumber is repeated in: " + assembly + " in " + mount
                    errorList.append(error)

    # Getting Final Excel Dictionary in Json
    list_Excel = {}
    list_Excel["Components"] = dict_Partnumbers
    list_Excel["AdditionalFeatures"] = dict_AdditionalFeatures

    # compare_json = json.dumps(list_Excel, indent=4, sort_keys=True)
    # End of Writing dictionaries to json

    print(rev_letter)
    print(str(int(compare_id)))
    print(''.join(errorList))
    print(list_Excel)

    return rev_letter, str(int(compare_id)), list_Excel, ''.join(errorList)
    # End of processing Excel
