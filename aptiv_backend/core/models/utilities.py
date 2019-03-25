import tabula, PyPDF2, re, os

# Utility fucntions
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
