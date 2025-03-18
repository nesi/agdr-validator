import xlrd
import os
import pandas as pd

DATADIR = "/Users/eirian/NeSI/2023-01-17-metadata-spreadsheet-validation/excelParser/test/data"
VENENIVIBRIO = "AGDR_Metadata_Venenivibrio.xlsx"
HOIHO = "AGDR_00029_Metadata_Hoiho_202208.xlsx"


#book = xlrd.open_workbook(os.path.join(DATADIR, VENENIVIBRIO))
##pdbook = pd.read_excel(os.path.join(DATADIR, VENENIVIBRIO))
#pdbook = []
#xls = pd.ExcelFile(os.path.join(DATADIR, VENENIVIBRIO))
#for i in range(len(tabs)):
#    pdbook.append(pd.read_excel(xls, tabs[i]))

class PrototypeReader(object):
    tabs = [
        "Project",
        "Experiments, Organisms",
        "Files and Instruments"
    ]
    def __init__(self):
        self.book = None
    def readBook(self, bookpath):
        #book = xlrd.open_workbook(bookpath)#os.path.join(DATADIR, VENENIVIBRIO))
        #pdbook = pd.read_excel(os.path.join(DATADIR, VENENIVIBRIO))
        pdbook = []
        xls = pd.ExcelFile(bookpath)#os.path.join(DATADIR, VENENIVIBRIO))
        for i in range(len(self.tabs)):
            pdbook.append(pd.read_excel(xls, self.tabs[i]))
        self.book = pdbook
        return pdbook


    def viewBook(self, index=None):
        print(type(self.book[1]))
        # retrieve rows 5 and 6
        print(self.book[1].loc[[5,6]])
        # get column names
        #print("---")
        #colNames = self.book[1].head()
        #print(colNames)
        print("---")

        # column headers for Experiments
        fields = self.book[1].loc[2,]
        print(fields)
        print("---")
        #fstcol = self.book[1].loc[,1]
        #print("---")
        #colNames = fields.columns
        #print(colNames)

        # could call .transpose, I'm wanting to know how to get columns
        # maybe it's not too important
        for f in dir(fields): print(f)

        print("---")
        for i in range(0, 5):
            for j in range(0, 5):
                pass
                #print(self.book[1].at[i,j])
                #print(self.book[1].loc[i].at[j])
                # hmmm
                print(self.book[1].loc[i].iat[j])
                # ok, this is how I do it
                # probably just want to iterate to parse AGDR notebook