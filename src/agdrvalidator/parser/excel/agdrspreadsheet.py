'''
@Author: Eirian Perkins

The purpose of this file is to parse AGDR spreadsheets. The spreadsheet 
templates are not currently versioned, but should be moving forward. 

The parsing depends on the AGDR spreadsheet format, and expects certain 
headers to be present. If there is a problem with validation, check 
the spreadsheet for the expected headers and column names
'''
from agdrvalidator.utils import logger
from agdrvalidator.utils.array import *
from agdrvalidator import AgdrFormatException
from agdrvalidator.parser import *
from agdrvalidator.utils.tabular import * # Table()
import pandas as pd

from alive_progress import alive_bar

logger = logger.setUp(__name__)

class Agdr(Parser):
    def __init__(self, datapath):
        super().__init__(datapath)
        self.PROJECT = "Project"
        self.EXP_ORG = "Experiments, Organisms"
        self.FILE_INST = "Files and Instruments"
        self.tabs = [
            self.PROJECT,
            self.EXP_ORG,
            self.FILE_INST
        ]

        # Project
        self.Project = Table()

        # Experiments, Organisms
        self.Experiments = Table()
        self.Organism = Table()
        self.Environmental = Table()

        # Files and Instruments
        self.Files = Table()
        self.InstrumentMetadata = Table()
        self.version = "0"

        self.book = self._openBook()


    def _extractVersion(self, excel):
        sheets = [x.lower().strip() for x in excel.sheet_names]
        version_tab = "nesi_internal_use"
        index = -1
        version = "0"
        if version_tab in sheets:
            index = sheets.index(version_tab)
        else:
            return version
        
        book = pd.read_excel(excel, index, header=None)
        rows, _ = book.shape
        for r in range(rows):
            row = book.loc[r,][0]
            if not row or not pd.notna(row) or str(row).lower() == "nan":
                continue
            cell = str(book.loc[r].iat[0]).strip()
            if "metadata template version" in cell.lower():
                continue
            if "please do not modify" in cell.lower():
                continue
            version = row

        return version



    def _openBook(self):
        bpath = self.datapath.split("/")[-1]
        bextension = bpath.split(".")[-1]
        logger.debug(f"file extension: {bextension.lower()}")
        if not bextension.lower() == "xlsx":
            raise Exception("File extension must be .xlsx")
        # check to see if it's excel, if not, throw error
        pdbook = []
        xls = pd.ExcelFile(self.datapath)
        for i in range(len(self.tabs)):
            try:
                # the date conversion is wrong, but may be 
                # a consequence of exporting from Google sheets
                pdbook.append(pd.read_excel(xls, self.tabs[i]))
            except:
                raise AgdrFormatException("File is not in AGDR format")
        self.version = self._extractVersion(xls)
        return pdbook

    def _parse_project(self, book):
        '''
        parse project info
        '''
        rows, columns = book.shape
        logger.debug(f"Rows: {rows}\tColumns: {columns}")
        shouldLogContent = False
        for r in range(rows):
            row = book.loc[r,]
            if row.isnull().all():
                continue
            cell = str(book.loc[r].iat[0]).strip()
            if cell == "Field":
                self.Project.header.append(list(row)[1:])
                shouldLogContent = True
                continue
            if cell == "Required field?":
                self.Project.required.append(list(row)[1:])
                shouldLogContent = True
                continue
            if cell == "Description":
                continue
            if cell == "Example input":
                continue
            if cell == "Instructions and tips":
                break
            if not shouldLogContent:
                continue
            if row.tail(-1).isnull().all():
                logger.debug("skipping row")
                continue
            row.where(pd.notnull(row), None, inplace=True)
            self.Project.data.append(list(row)[1:])


    def _parse_exp_org(self, book):
        '''
        parse experiment and biosample info
        '''
        rows, columns = book.shape
        logger.debug(f"Rows: {rows}\tColumns: {columns}")
        shouldLogContent = False
        currentTable = None

        for r in range(rows):
            row = book.loc[r,]
            #logger.debug(list(row))
            # no point in checking for nan's twice
            # we check if row is blank after checking "header" values
            # in the if blocks below
            #
            #if row.isnull().all():
            #    logger.debug("skipping row")
            #    continue
            cell = str(book.loc[r].iat[0]).strip()
            logger.debug(cell)
            if cell == "Experiments" or "Experiments done within the project" in cell:
                currentTable = self.Experiments
                continue
            if cell == "Type:Organism":
                currentTable = self.Organism
                continue
            if cell == "Type:Environmental" or cell == "Type:Metagenome":
                currentTable = self.Environmental
                continue
            if cell == "Biosamples":
                shouldLogContent = False
                continue
            # user may have accidentally copied this, 
            # we're chopping the head off so it doesn't matter
            #if cell == "Add more rows as needed":
            #    shouldLogContent = False
            #    continue
            if cell == "Field":
                shouldLogContent = True
                currentTable.header.append(list(row)[1:])
                continue
            if cell == "Required field?":
                shouldLogContent = True
                currentTable.required.append(list(row)[1:])
                continue
            if cell == "Description":
                continue
            if cell == "Example input":
                continue
            if not shouldLogContent:
                continue
            logger.debug(list(row))
            if row.tail(-1).isnull().all():
                logger.debug("skipping row")
                continue
            row.where(pd.notnull(row), None, inplace=True)
            # remove trailing nan or None in a row
            #logger.info(f"_____header pre: {currentTable.header}")
            currentTable.header = [chomp(currentTable.header[0])]
            #logger.info(f"_____header post: {currentTable.header}")
            length = len(currentTable.header[0])
            # chop off "your input" from start of row
            #currentTable.data.append(list(row)[1:])
            crow = chomp_front(list(row)[1:])
            currentTable.data.append(crow[:length])



    def _parse_file_inst(self, book):
        '''
        parse file and instrument info
        '''
        rows, columns = book.shape
        logger.debug(f"Rows: {rows}\tColumns: {columns}")
        shouldLogContent = False
        currentTable = None

        for r in range(rows):
 
            row = book.loc[r,]
            #logger.debug(list(row))
            # no point in checking for nan's twice
            # we check if row is blank after checking "header" values
            # in the if blocks below
            #
            #if row.isnull().all():
            #    logger.debug("skipping row")
            #    continue
            cell = str(book.loc[r].iat[0]).strip()
            logger.debug(cell)
            if cell == "Files" or "Files generated from experiments" in cell:
                currentTable = self.Files
                continue
            if "Instrument metadata" in cell:
                currentTable = self.InstrumentMetadata
                shouldLogContent = False
                continue
            if cell == "Field":
                shouldLogContent = False
                currentTable.header.append(list(row)[1:])
                continue
            if cell == "Required field?":
                shouldLogContent = True
                currentTable.required.append(list(row)[1:])
                continue
            if cell == "Description":
                continue
            if cell == "Format":
                shouldLogContent = False
                continue
            if cell == "Example input":
                continue
            if cell == "Your input":
                shouldLogContent = True
            if not shouldLogContent:
                continue
            logger.debug(list(row))
            if row.tail(-1).isnull().all():
                logger.debug("skipping row")
                continue
            row.where(pd.notnull(row), None, inplace=True)
            currentTable.data.append(list(row)[1:])



    def parse(self):
        with alive_bar(title="\tParsing AGDR spreadsheet", length=len(self.tabs)) as bar:
            for index, tabName in enumerate(self.tabs):
                logger.debug(f"tabName: {tabName}")
                logger.debug(f"index: {index}")
                if tabName == self.PROJECT:
                    self._parse_project(self.book[index])
                elif tabName == self.EXP_ORG:
                    self._parse_exp_org(self.book[index])
                elif tabName == self.FILE_INST:
                    self._parse_file_inst(self.book[index])
                bar()



