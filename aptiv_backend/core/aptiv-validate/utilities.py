import tabula
import PyPDF2
import re
import os
import xlrd
import json


# Error functions
path_error = "files/Errors_List.txt"
def create_ErrorFile():         # creates a text file for error output
    error_file = open(path_error,"w+")
    error_file.close()


def add_error_item(error):          # adds error line to error text file
    error_file = open(path_error, "a")
    error_file.write(error + "\n")
    error_file.close()

def noErrors():         # checks if there were no added errors to
    if os.stat(path_error).st_size == 0:
        add_error_item("No errors/ warnings")
# End of error functions



# Parsing PDF to python functions
def pageValidation(page):           # checks if page is useful (the pages that have useful tables all have the following string in the the same postion)"
    aux = False
    for x in range(0,len(page) - 1):
        if page[x][0][0] == "If Package name is not available, then up to 15 characters of the geometry name\rwill appear in parentheses":
         aux = True
    if not aux:         # unuseful pages are marked as ignore
        page = "ignore"
    return page


def ignore_complete(pages):  # #CMP table is not necessary to analyse
    n_pages = len(pages)
    pageNumber = n_pages
    aux = False

    while not aux and pageNumber > -1:          # assuming that CMP page is either last page or is only before ignorable pages
        if pages[pageNumber - 1] == "ignore":
            pageNumber = pageNumber - 1
        else:
            pages[pageNumber - 1] = "ignore"
            aux = True
    return pages


def numPages(path):         #gets number of pages id the PDF file
    from PyPDF2 import PdfFileReader
    pdf_file = open(path, 'rb')
    pdf_reader = PdfFileReader(pdf_file)
    n_pages = PdfFileReader.getNumPages(pdf_reader)
    return n_pages


def pdf_to_tb(path, page):
    dt = tabula.read_pdf(path, output_format="dataframe", encoding="utf-8", java_options=None, pandas_options=None,
                         multiple_tables=True, pages=page)
    return dt  #returns list of the multiple dataframes inside a page

def pdf_to_tb_area(path, page, xl,yl, xr,yr):  # returns list of dataframes for a specific area
    df = tabula.read_pdf(path, output_format="dataframe", encoding="utf-8", java_options=None, pandas_options=None,
                         multiple_tables=True, pages=page, spreadsheet=True, area=(xl,yl,xr,yr))
    return df

def pdf_to_tb_noPage(path):
    dt = tabula.read_pdf(path, output_format="dataframe", encoding="utf-8", java_options=None, pandas_options=None,
                         multiple_tables=True)
    return dt  #returns list of the multiple dataframes inside a page



def getPages(path):
    n_pages = numPages(path)
    pages=[]   #list that stores pages
    pages.append(pdf_to_tb(path,1))
    pages[0].append(pdf_to_tb_area(path, 1, 73.01,1743.3,1682.21,2363.14)) #retira info da tabela das datas
    for x in range(2, n_pages +1):
        page = pdf_to_tb_area(path,x, 34.27,32.78,1649.43,2360.16) #retira informação dentro dos limites da grelha
        page = pageValidation(page)
        pages.append(page)
    pages = ignore_complete(pages)
    return pages
# End of Parsing PDF to python functions



# 2 get assemlies with last revision and dataframes for each mount
def rev_error(page):
    dataframe = page[3]
    startColumn = check_start_column(dataframe)
    list_Finders = []
    list_Rev = []

    for row in range(len(dataframe[0])-1, -1, -1):
        if type(dataframe[startColumn][row]) != float:
            if "." in dataframe[startColumn][row]:
                revLetter = dataframe[startColumn+3][row]
                list_Rev.append(revLetter)
                list_Finders.append(list_Rev)
                list_Rev.reverse()
                list_Rev = []
            else:
                revLetter = dataframe[startColumn+3][row]
                list_Rev.append(revLetter)

    list_Finders.reverse()



    for finder in range(len(list_Finders)):
        counter = 0
        last_Rev = list_Finders[finder][0]
        for revision in range(1, len(list_Finders[finder])):
            revLetter = list_Finders[finder][revision]
            if revLetter == last_Rev:
                counter+=1
            elif revLetter >= last_Rev:
                error = "Error: Assembly in position " + str(revision +1) + " has later revision than CMP in finder "+ str(finder + 1)
                add_error_item(error)
        if counter == 0:
            warning = "Warning: CMP has later revision than all assemblies in finder " + str(finder +1)
            add_error_item(warning)


def select_data(pages):
    data_list=[]

    n_pages = len(pages)
    i = n_pages

    aux = False
    i = 0
    while i < n_pages:
        if pages[i] == "ignore":
            if not i == n_pages-1:
                if not pages[i+1] == "ignore":
                    array = []
                    x = i +1
                    while pages[x] != "ignore":
                        array.append(pages[x])
                        x += 1
                    i = x - 1
                    data_list.append(array)
        i = i + 1
    return data_list

#checks at which column starts the partnumbers
def check_start_column(dataframe):
    aux = False
    x = -1
    while not aux:
        x += 1
        if not type(dataframe[x][0]) == float:
             if not re.match('\d{5,}', dataframe[x][0]): #cell has to have 5 or more digits
                aux= True
    return  x


#returns boolean, wether each mount appears or not
def get_mounts(dataframe): #checks if there is SM1, SM2, HP1 in initial table
    start_column = check_start_column(dataframe)
    existsSM1 = False
    existsSM2 = False
    existsHP1 = False
    for x in range(len(dataframe[0])):
        if not type(dataframe[start_column + 1][x]) == float:
            if "SM1" in dataframe[start_column + 1][x]:
                existsSM1 = True
            elif "SM2" in dataframe[start_column + 1][x]:
                existsSM2 = True
            elif "HP1" in dataframe[start_column + 1][x]:
                existsHP1 = True
    return  existsSM1,  existsSM2, existsHP1



#returns list
def mounts_list(pages):
    list = []
    sm1, sm2, hp1 = get_mounts(pages[0][3]) #page 0 is the first one, and the info is in dataframe number 3, always
    if sm1:
        list.append("SM1")
    if sm2:
        list.append("SM2")
    if hp1:
        list.append("HP1")
    return list



def retrieve(path, pages):

    rev_letter = rev(pages[0])
    data_list = select_data(pages)
    mount_list = mounts_list(pages)
    verticalAssemblyList = retrieve_data(path, pages)
    rev_error(pages[0])

    return rev_letter, data_list, mount_list, verticalAssemblyList

def rev(page):
    x = 0
    while x <= len(page[5][0][2]):
        rev = page[5][0][2][x]
        aux = True
        for i in range (x+1, x + 6):
            if not type(page[5][0][2][i]) == float:
                aux=False
        if aux:
            if not type(rev) == float:
                x = len(page[5][0][2])
        x +=1
    return rev

#rotates all pdf pages
def rotate(path, path_out, degrees):
    pdf_in = open(path, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_in)
    pdf_writer = PyPDF2.PdfFileWriter()

    for pagenum in range(pdf_reader.numPages):
        page = pdf_reader.getPage(pagenum)
        page.rotateClockwise(degrees)
        pdf_writer.addPage(page)

    pdf_out = open(path_out, 'wb')
    pdf_writer.write(pdf_out)
    pdf_out.close()
    pdf_in.close()



#gets an array of assemblies that will correspond to a mount
def getList(path,pagenum):
    page = pdf_to_tb_area(path, pagenum, 28.418,1444.03,2352.338,1652.425) #retrieves by area

    assemblyArray = []
    aux = True
    i = 0
    while aux:
        assemblyArray.append(page[0][0][i])
        number = page[0][0][i+1]
        if not type(number) == float:  # drop all float values… … but only if they are nan
            if not re.match('\d{5,}', number): #checks if string has 5 digits or more, if not it ends the cycle
                aux = False
        else:
            aux = False
        i +=1

    return assemblyArray



#agreggates the assemblies arrays in a list
def retrieve_data(path, pages):
    path_out = 'files/rotated.pdf'
    rotate(path,path_out, 90)


    checkAssembly_list = []
    for pagenum in range(len(pages)-1, 1, -1):
        if pages[pagenum] == "ignore":
            if not pages[pagenum - 1] == "ignore":
                checkAssembly_list.append(getList(path_out, pagenum))

    checkAssembly_list.reverse()
    os.remove(path_out)
    return checkAssembly_list



#creates deictionary, keys are mounts and the data ara the respective pages of that mount
def assoc(data_list, mount_list):
    dict = {}
    for i in range(len(data_list)):
        dict[mount_list[i]] = data_list[i]
    if not len(data_list) == len(mount_list):
        add_error_item("Not every mount from 1st page is defined through out PDF or otherwise, rest of analysis might be corrupted")
    return dict

#checks which rows have the latest revision
def last_revision_positions(rev_letter,dataframe, start_column):
    column = start_column + 3
    positions = []
    for x in range(len(dataframe[column])):
        if dataframe[column][x] == rev_letter:
            positions.append(x)
    return positions


#adds to respective mounts, the assemblies that are signelized as being last revised, this is the make up of my final dictionary
def function_revAssembliesList(pages, rev_letter):
    dataframe = pages[0][3]
    assemblyList = {"SM1": [], "SM2": [], "HP1": []}
    start_column = check_start_column(dataframe)
    positions = last_revision_positions(rev_letter,dataframe, start_column)
    for value in positions:
        if "SM1" in dataframe[start_column + 1][value]:
            assemblyList["SM1"].append(dataframe[start_column][value])
            sorted(assemblyList["SM1"])
        elif "SM2" in dataframe[start_column + 1][value]:
            assemblyList["SM2"].append(dataframe[start_column][value])
            sorted(assemblyList["SM2"])
        elif "HP1" in dataframe[start_column + 1][value]:
            assemblyList["HP1"].append(dataframe[start_column][value])
            sorted(assemblyList["HP1"])

    return assemblyList



def number_vertical_assemblys(verticalAssemblyDict):
    total_columns = {}
    for key in verticalAssemblyDict:
        total_columns[key] = len(verticalAssemblyDict[key])
    return total_columns


def columns_to_analyze(revAssemblyList, verticalAssemblyDict):
    positions = {"SM1" : {}, "SM2" : {}, "HP1" : {} }
    total_columns = number_vertical_assemblys(verticalAssemblyDict)
    for mount in revAssemblyList:
        if revAssemblyList[mount] is not None:
            if mount in verticalAssemblyDict:
                for i in range(total_columns[mount]):
                    if verticalAssemblyDict[mount][i] in revAssemblyList[mount]:
                        positions[mount][verticalAssemblyDict[mount][i]] = i
    return positions


def final_dictionary(dictFile, revAssembliesList, positions, verticalAssemblyDict):
    dict = {}
    optional_dict = {}
    additional_features_dict ={}
    optional_features_dict = {}
    for mount in revAssembliesList:
        if revAssembliesList[mount] != []:
            dict[mount] = {}
            optional_dict[mount] = {}
            additional_features_dict[mount] = {}
            optional_features_dict[mount] = {}
            for assembly in range(len(revAssembliesList[mount])):
                dict[mount][revAssembliesList[mount][assembly]] = {}
                optional_dict[mount][revAssembliesList[mount][assembly]] = {}
                additional_features_dict[mount][revAssembliesList[mount][assembly]] ={}
                optional_features_dict[mount][revAssembliesList[mount][assembly]]= {}
                for page in range(len(dictFile[mount])):
                    for table in range(len(dictFile[mount][page])):
                        if checkDataframe(dictFile[mount][page][table], len(verticalAssemblyDict[mount])):
                            dataframe = dictFile[mount][page][table]
                            partnumbers, optional_partnumbers, additional_features, optional_features, error = get_partnumbers(dataframe, positions[mount][revAssembliesList[mount][assembly]], len(verticalAssemblyDict[mount]))
                            add_error(error)
                            for value in partnumbers:
                                if not value in dict[mount][revAssembliesList[mount][assembly]]:
                                    dict[mount][revAssembliesList[mount][assembly]][value] = partnumbers[value]
                                else:
                                    dict[mount][revAssembliesList[mount][assembly]][value]["qty"] += partnumbers[value]["qty"]
                            for value in optional_partnumbers:
                                if not value in optional_dict[mount][revAssembliesList[mount][assembly]]:
                                    optional_dict[mount][revAssembliesList[mount][assembly]][value] = optional_partnumbers[value]
                                else:
                                    optional_dict[mount][revAssembliesList[mount][assembly]][value]["qty"] += optional_partnumbers[value]["qty"]
                            for value in additional_features:
                                if not value in additional_features_dict[mount][revAssembliesList[mount][assembly]]:
                                    additional_features_dict[mount][revAssembliesList[mount][assembly]][value] = additional_features[value]
                                else:
                                    additional_features_dict[mount][revAssembliesList[mount][assembly]][value]["qty"] += additional_features[value]["qty"]

                            for value in optional_features:
                                if not value in optional_features_dict[mount][revAssembliesList[mount][assembly]]:
                                    optional_features_dict[mount][revAssembliesList[mount][assembly]][value] = optional_features[value]
                                else:
                                    optional_features_dict[mount][revAssembliesList[mount][assembly]][value]["qty"] += optional_features[value]["qty"]
    return dict, optional_dict, additional_features_dict, optional_features_dict


def checkDataframe(dataframe, start_column):
    temp = False
    x = len(dataframe.columns)
    y = start_column
    if len(dataframe.columns) - start_column == 4:
        temp = True
    return temp



def get_start_row(dataframe):
    for x in range(len(dataframe[0])):
        if type(dataframe[0][x]) == float:
            if type(dataframe[0][x+1]) != float:
                x = x +1
                break
    return x


def add_PartnumberToDictionary(partnumber, description, dictionary):
    added = True
    if partnumber in dictionary:
        dictionary[partnumber]["qty"] += 1
        if dictionary[partnumber]["description"] != description:
            added = False

    else:
        dictionary[partnumber] = {"qty": 1, "description": description}
    return added


def get_partnumbers(dataframe, col, nColumns_toCheck):
    partnumbers = {}
    optional_partnumbers = {}
    additionalFeatures = {}
    optional_addtionalFeatures = {}
    error = "nothing"
    start_row = get_start_row(dataframe)

    for row in range(start_row, len(dataframe[0])):
        added = True
        if dataframe[col][row]=="1":
            partnumber = dataframe[nColumns_toCheck + 1][row]
            description = dataframe[nColumns_toCheck + 2][row]
            if "MA" in partnumber: #checks if is an additional feauture
                added = add_PartnumberToDictionary(partnumber, description, additionalFeatures)
            elif not "LOCAL_FID" in partnumber and not "GLOBAL_FID"  in partnumber:
                added = add_PartnumberToDictionary(partnumber, description, partnumbers)
            if not added:
                error = "Warning: Component: ", partnumber, "has different descriptions"
                add_error(error)
        elif dataframe[col][row] == "O01":
            partnumber = dataframe[nColumns_toCheck + 1][row]
            description = dataframe[nColumns_toCheck + 2][row]
            if "MA" in partnumber: #checks if is an additional feauture
                added = add_PartnumberToDictionary(partnumber, description, optional_addtionalFeatures)
            elif not "LOCAL_FID" in partnumber and not "GLOBAL_FID" in partnumber:
                added = add_PartnumberToDictionary(partnumber, description, optional_partnumbers)
            if not added:
                error = "Warning: Component: ", partnumber, "has different descriptions"
                add_error(error)
    return partnumbers, optional_partnumbers, additionalFeatures, optional_addtionalFeatures, error


def add_error(error):
    if error != "nothing":
        add_error_item(error)



#PDF Main

def PDF(path):
#create error file


    #stage 1
    # with this command we get all pages in a lsit. Each page is a list of dataframes containing all useful info. The pages that have no useful info are a string "ignore"
    pages = getPages(path)

    pass



    #stage 2
    #retrieve last rev letter, retrive list with separeted data, retrive mount list(checking which mounts are in pdf file)
    rev_letter, data_list, mount_list, verticalAssemblyList = retrieve(path, pages)

    pass


    #stage3
    #associates data_list with mounts, returning the dictionary which will be analised
    dictFile = assoc(data_list, mount_list)
    verticalAssemblyDict = assoc(verticalAssemblyList, mount_list)

    revAssembliesList = function_revAssembliesList(pages, rev_letter)

    pass


    #stage4
    #getting the columns positions to check in each mount
    positions = columns_to_analyze(revAssembliesList, verticalAssemblyDict)




    #stage5
    #buliding the full dictionary
    dict_FinalDataFile, dict_OptionalFinalDataFile, dict_AdditionalFeatures, dict_OptionalAdditionalFeatures = final_dictionary(dictFile,revAssembliesList, positions, verticalAssemblyDict)

    f = open("files/InsertedComponents.json", "w+")
    f.write("Last Revision = " + rev_letter + "\n")
    f.write(json.dumps(dict_FinalDataFile, indent=4, sort_keys=True))
    f = open("files/OptionalComponents.json", "w+")
    f.write("Last Revision = " + rev_letter + "\n")
    f.write(json.dumps(dict_OptionalFinalDataFile, indent=4, sort_keys=True))
    f = open("files/InsertedAdditionalFeatures.json", "w+")
    f.write("Last Revision = " + rev_letter + "\n")
    f.write(json.dumps(dict_AdditionalFeatures, indent=4, sort_keys=True))
    f = open("files/OptionalAdditionalFeatures.json", "w+")
    f.write("Last Revision = " + rev_letter + "\n")
    f.write(json.dumps(dict_OptionalAdditionalFeatures, indent=4, sort_keys=True))
    pass


    list_PDF = []
    list_PDF.append(dict_FinalDataFile)
    list_PDF.append(dict_OptionalFinalDataFile)
    list_PDF.append(dict_AdditionalFeatures)
    list_PDF.append(dict_OptionalAdditionalFeatures)

    return list_PDF



#Excel

# 1 get Assmeblies and tables


def get_all(path):

    book = xlrd.open_workbook(path)
    sheet_EBOM_DATA = book.sheet_by_name("EBOM Data")
    sheet_IMD = book.sheet_by_name("ITEM MASTER Data")
    dict_RevAssemblies = get_RevAssemblies(sheet_IMD)
    dict_DataList=  get_DataList(sheet_EBOM_DATA)

    return dict_RevAssemblies, dict_DataList



def get_RevAssemblies(sheet):
    dict_RevAssembly = {"SM1" : {}, "SM2" : {}, "HP1" : {}, "CMP" : {}}
    n_rows = sheet.nrows
    for row in range(7, n_rows): #table starts at line 7
        name = sheet.cell(row, 0).value
        assembly = get_assembly(name)
        item_name = sheet.cell(row, 1).value
        if "SM1" in item_name:
            dict_RevAssembly["SM1"][assembly] = item_name
        elif "SM2" in item_name:
            dict_RevAssembly["SM2"][assembly] = item_name
        elif "HP1" in item_name:
            dict_RevAssembly["HP1"][assembly] = item_name
        elif "CMP" in item_name:
            dict_RevAssembly["CMP"][assembly] = item_name


    return dict_RevAssembly


def get_assembly(name):

    lenth_assembly=0
    for chr in range(len(name)):
        if name[lenth_assembly]==",":
            break
        else:
            lenth_assembly += 1

    assembly=name[:(lenth_assembly)]
    return assembly


def get_DataList(sheet_EBOMData):
    list_Assemblies = Get_Assemblies(sheet_EBOMData)
    dict_DataList = {"SM1" : {}, "SM2" : {}, "HP1" : {}, "CMP" : {}}
    nRows = sheet_EBOMData.nrows
    for list_index in range(len(list_Assemblies)-1): # nao verifica a última tabela
        Assembly= list_Assemblies[list_index][1] #assembly number
        list_dataList=[]

        assemblyRow = list_Assemblies[list_index][0] #position 0 of array in list is the row number
        start_row = get_StartRow(sheet_EBOMData, assemblyRow, nRows)
        end_row = list_Assemblies[list_index+1][0]-2  #table ends 3 rows above partnumber
        for row in range(start_row, end_row):
            lineData = sheet_EBOMData.row_values(row, 1, 7)
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
        dict_DataList[mount][Assembly] = list_dataList


    #last table
    assemblyRow = list_Assemblies[len(list_Assemblies) - 1][0]
    start_row = get_StartRow(sheet_EBOMData, assemblyRow, nRows)
    end_row = sheet_EBOMData.nrows
    Assembly = list_Assemblies[len(list_Assemblies)-1][1]
    list_dataList = []
    for row in range(start_row, end_row):
        lineData = sheet_EBOMData.row_values(row, 1, 7)
        list_dataList.append(lineData)

    description = list_Assemblies[len(list_Assemblies)-1][2]
    mount = ""
    if "SM1" in description:
        mount = "SM1"
    elif "SM2" in description:
        mount = "SM2"
    elif "HP1" in description:
        mount = "HP1"
    elif "CMP" in description:
        mount = "CMP"
    dict_DataList[mount][Assembly] = list_dataList

    return dict_DataList



def get_StartRow(sheet, AssemblyRow, lenth_sheet):
    for row in range(AssemblyRow, lenth_sheet):
        x = sheet.cell(row, 0)
        if sheet.cell(row, 0).value == "Ll":
            startRow = row+1
            break
    return startRow




def Get_Assemblies(sheet_EBOM_data):
    list_Assemblies=[]
    nrows = sheet_EBOM_data.nrows
    for row in range(nrows):
        if sheet_EBOM_data.cell(row, 0).value=="Part Number":
            list_Assemblies.append([row, sheet_EBOM_data.cell(row, 1).value, sheet_EBOM_data.cell(row+3, 1).value])
    return list_Assemblies #contains star row, assembly number and assembly description


def checkCoherence(dict_RevAssemblies, dict_DataList):
    for mount in dict_RevAssemblies:
        for assembly in dict_RevAssemblies[mount]:
            if not assembly in dict_DataList[mount]:
                error = "Error: Assembly: " + str(assembly) + " , " + str(mount) + " from ITEM MASTER Data is not present in " + str(mount) + " in EBOM Data"
                add_error_item(error)


def checkCMP(dict_DataList):
    if dict_DataList["CMP"] != {}:
        retrieveData(dict_DataList["CMP"])






def retrieveData(dict_CMPAssemblies):
    for assembly in dict_CMPAssemblies:
        edd, dwg, schematic = get_Features(dict_CMPAssemblies[assembly])
        if edd != "" or dwg != "" or schematic != "":
            error = "Assembly: " + assembly + " => CMP is missing " + edd + " " +  dwg + " " + schematic
            add_error_item(error)


def get_Features(list_assemblies):  # número part number

    edd = "EDD"
    dwg = "DWG"
    schematic = "SCHEMATIC"
    for part in range(len(list_assemblies)):
        partnumber =list_assemblies[part][1]
        description = list_assemblies[part][3]
        if "EDD" in partnumber:
            edd = ""
        elif "DWG" in partnumber:
            dwg = ""
        elif "SCHEMATIC" in description:
            schematic = ""
    return edd, dwg, schematic


def final_dict(dict_Tables):
    dict_Partnumbers = {}
    dict_AdditionalFeatures = {}
    for mount in dict_Tables:
        dict_Partnumbers[mount]={}
        dict_AdditionalFeatures[mount]={}
        for assembly in dict_Tables[mount]:
            dict_Partnumbers[mount][assembly] ={}
            dict_AdditionalFeatures[mount][assembly] = {}
            table = dict_Tables[mount][assembly]
            partnumbers, additional_features = get_partnumbersExcel(table)
            for value in partnumbers:
                if not value in dict_Partnumbers[mount][assembly]:
                    dict_Partnumbers[mount][assembly][value] = partnumbers[value]
                else:
                    erro = "Partnumber repetida em: " + assembly + " em " + mount
            for value in additional_features:
                if not value in dict_AdditionalFeatures[mount][assembly]:
                    dict_AdditionalFeatures[mount][assembly][value] = additional_features[value]
                else:
                    erro = "Partnumber repetida em: " + assembly + " em " + mount

    return dict_Partnumbers, dict_AdditionalFeatures




def get_partnumbersExcel(table):
    partnumbers = {}
    additional_features = {}
    for item in range(len(table)):
        IsNumber=re.match('\d{1,}', table[item][0]) #check if there are digits in de F/N column
        if IsNumber:
            number = table[item][1]
            description = table[item][3]
            if not table[item][5]=="PC":
                additional_features[number] = {"qty" : 1, "description" : description}
            else:
                qty = table[item][4]
                partnumbers[number] = {"qty": qty, "description": description}
    return partnumbers, additional_features



#Excel Main

def EXCEL(path):
    #stage 1 - collect assemblies revised and collect independent tables
    dict_RevAssemblies, dict_DataList = get_all(path)
    pass


    #stage 2 - Checks coherence between ITEM MASTER Data and EBOM Data.
    checkCoherence(dict_RevAssemblies, dict_DataList)


    #stage 3 - Checks if all the needed components in CMP are in place (DWG,EDD and SCHEMATIC), retrieves and filters Part Numbers, getting the final dictionary to compare with PDF File.
    checkCMP(dict_DataList)
    dict_Partnumbers, dict_AdditionalFeatures = final_dict(dict_DataList)
    pass


    f = open("files/ExcelPartnumbers.json", "w+")
    f.write(json.dumps(dict_Partnumbers, indent=4, sort_keys=True))
    f = open("files/ExcelAdditionalFeatures.json", "w+")
    f.write(json.dumps(dict_AdditionalFeatures, indent=4, sort_keys=True))
    pass

    list_Excel = []
    list_Excel.append(dict_Partnumbers)
    list_Excel.append(dict_AdditionalFeatures)

    return list_Excel


#compare

def compare(list_PDF, list_Excel):  # Pdf has 4 dict and excel has 2
    dictPDF_Components = list_PDF[0]
    dictPDF_OptComponents = list_PDF[1]
    dictPDF_AdditionalFeatures = list_PDF[2]
    dictPDF_OptAdditionalFeatures = list_PDF[3]
    dictExcel_Components = list_Excel[0]
    dictExcel_AdditionalFeatures = list_Excel[1]
    check_Partnumbers(dictPDF_Components, dictPDF_OptComponents, dictExcel_Components) #validation of inserted components
    check_Partnumbers(dictPDF_AdditionalFeatures, dictPDF_OptAdditionalFeatures, dictExcel_AdditionalFeatures) #validation of inserted addtional features




def check_Partnumbers(dictPDF_Partnumbers, dictPDF_OptPartnumbers,  dictExcel_Partnumbers):
    for mount in dictPDF_Partnumbers:
        for assembly in dictPDF_Partnumbers[mount]:
            for partnumber in dictPDF_Partnumbers[mount][assembly]:
                if existsInDictionary(partnumber, assembly, mount, dictExcel_Partnumbers): #cheks if it exists in excel
                    checkDescription(partnumber, assembly, mount, dictPDF_Partnumbers, dictExcel_Partnumbers)
                    checkQty(partnumber, assembly, mount, dictPDF_Partnumbers, dictPDF_OptPartnumbers, dictExcel_Partnumbers)
                    del dictExcel_Partnumbers[mount][assembly][partnumber]
                else:
                    error = "ERROR: Partnumber " + partnumber + " does not exist in assembly " + assembly + " " + mount + " in Excel"
                    add_error_item(error)




def checkDescription(partnumber, assembly, mount, dictPDF_Partnumbers, dictExcel_Partnumbers):
    descriptionPDF = dictPDF_Partnumbers[mount][assembly][partnumber]["description"]
    descriptionExcel = dictExcel_Partnumbers[mount][assembly][partnumber]["description"]
    if descriptionPDF != descriptionExcel:
        errorDisc(partnumber, assembly, mount)

def checkQty(partnumber, assembly, mount, dictPDF_Partnumbers, dictPDF_OptPartnumbers, dictExcel_Partnumbers):
    qtyPDF = int(dictPDF_Partnumbers[mount][assembly][partnumber]["qty"])
    qtyExcel = int(dictExcel_Partnumbers[mount][assembly][partnumber]["qty"])
    if qtyPDF > qtyExcel:
        errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF)
    elif qtyPDF < qtyExcel:
        compareOPT(partnumber, assembly, mount, dictPDF_Partnumbers, dictPDF_OptPartnumbers,dictExcel_Partnumbers)



def compareOPT(partnumber, assembly, mount, dictPDF_Partnumbers, dictPDF_OptPartnumbers,dictExcel_Partnumbers):
    qtyPDF = (dictPDF_Partnumbers[mount][assembly][partnumber]["qty"])
    qtyExcel = (dictExcel_Partnumbers[mount][assembly][partnumber]["qty"])
    qtyOPT = (dictPDF_OptPartnumbers[mount][assembly][partnumber]["qty"])
    if not existsInDictionary(partnumber, assembly, mount, dictPDF_OptPartnumbers):
        errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF)
    else:
        qty_OPTplusInserted = qtyPDF + qtyOPT
        if qtyExcel > qty_OPTplusInserted: #checks if qty in excel is higher than the sum of mandatory partnumbers and optional
            errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF)


def existsInDictionary(partnumber, assembly, mount, dictionary):
    aux = False
    if mount in dictionary:
        if assembly in dictionary[mount]:
            if partnumber in dictionary[mount][assembly]:
                aux = True
    return aux

def errorQTY(partnumber, assembly, mount, qtyExcel, qtyPDF):
    error = "ERROR: Quantity of partnumber " + partnumber + " in assembly " + assembly + " " + mount + " in Excel: "\
            +  str(qtyExcel) + " different from quantity in PDF: " + str(qtyPDF)
    add_error_item(error)

def errorDisc(partnumber, assembly, mount):
    error = "WARNING: Description of partnumber " + partnumber + " in assembly " + assembly + " " + mount + " does not match between PDF and Excel"
    add_error_item(error)

