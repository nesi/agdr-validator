'''
@Author: Eirian Perkins

The purpose of this file is to parse AGDR spreadsheets. The spreadsheet 
templates are currently versioned. This file is for the 2024-08-28 version 
of the AGDR metadata template, which corresponds to the 2024-09-10 version 
of the AGDR metadata dictionary.
'''
from agdrvalidator.utils import logger
from agdrvalidator.utils.array import *
from agdrvalidator import AgdrFormatException, BadMetadataSpreadhsheetException
from agdrvalidator.parser import *
from agdrvalidator.utils.rich_tabular import * 
import pandas as pd
import openpyxl

from alive_progress import alive_bar

logger = logger.setUp(__name__)


class Agdr(Parser):
    def __init__(self, datapath):
        self.datapath = datapath
        self.tabs = ["project",
                     "experiments_genomic",
                     "experiments_metagenomic",
                     "samples",
                     "files_instruments",
                     "NeSI_internal_use"]
        self.pyxl     = self._open_pyxl() # openpyxl workbook
        self.pd_excel = self._open_book() # pandas excel file
        self.required_color = 'FFD9EAD3'
        self.version = self._parse_nesi_internal_use()
        # dictionary of node name -> SpreadsheetNode object
        self.nodes = {}

    def _seek(self, sheet_name, text):
        '''
        helper method for finding a "table" within a sheet, like 
        Project Information, Dataset, Contributors, etc.
        '''
        # in the first column, find the row with the text
        # want to return row number, so the callee knows 
        # where to start parsing
        sheet = pd.read_excel(self.pd_excel, sheet_name)
        rows, _ = sheet.shape
        for r in range(rows):
            cell_text = str(sheet.loc[r].iat[0]).strip()
            if cell_text.lower() == text.lower():
                return r
        else:
            e = f"Could not find {text} in sheet"
            raise BadMetadataSpreadhsheetException(e)

    def _seek_fields(self, sheet_name, startrow) -> SpreadsheetRow:
        '''
        helper node for extracting "headers" from a "table" like 
        Project Information or Dataset

        should only be called by self._seek_data()

        must return a SpreadsheetRow object
        '''
        sheet = pd.read_excel(self.pd_excel, sheet_name)
        rows, _ = sheet.shape
        text = "Field"
        row = None
        for row in range(startrow, rows):
            cell_text = str(sheet.loc[row].iat[0]).strip()
            if cell_text.lower() == text.lower():
                break
        else:
            e = f"Could not find {text} in sheet"
            raise BadMetadataSpreadhsheetException(e)

        # extract all entries in the current row
        data = []
        fields = list(sheet.loc[row].dropna().values)
        for i in range(1, len(fields)):
            fields[i] = fields[i].strip()
            # cell position is row, i+1
            cl = CellLocation(row+2, i+1)
            cell = self.pyxl[sheet_name][str(cl)]
            fill_color = cell.fill.start_color.index
            required = self.required_color == fill_color
            sp = SpreadsheetProperty(fields[i], None, cl, required)
            data.append(sp)
        #return fields[1:]
        return SpreadsheetRow(data, sheet_name)


    #def _seek_data(self, sheet_name, startrow, headers):
    def _seek_data(self, sheet_name, startrow):
        '''
        helper method for extracting data for a particular node
        '''
        sheet = pd.read_excel(self.pd_excel, sheet_name)
        headers = self._seek_fields(sheet_name, startrow)
        self.headers = headers

        rows, _ = sheet.shape
        text = "Your input"
        data = []
        datastart = None
        for r in range(startrow, rows):
            cell_text = str(sheet.loc[r].iat[0]).strip()
            if cell_text.lower() == text.lower():
                datastart = r
                break
        else:
            if datastart == None:
                e = f"Could not find {text} in sheet"
                raise BadMetadataSpreadhsheetException(e)

        # now extract all rows of data until the row is empty
        for r in range(datastart, rows):
            
            # don't do this, it removes all None values (unpopulated cells)
            # what we want is to remove all None values at the end of the row
            #row = list(sheet.loc[r].dropna().values)[1:]

            #while row and pd.isna(row[-1]):
            #    row.pop()
            # the above is actually wrong, I want to stop popping rows
            # when I hit the same length as the headers
            row = list(sheet.loc[r].values)[1:]
            row = row[:len(headers.data)]
            logger.debug(f"row: {row}")

            if pd.isna(row).all() or not row:
                break

            sp = None
            spreadsheet_rows = []
            for index, value in enumerate(row):
                logger.debug(f"r: {r}, index: {index}")
                cl = CellLocation(r+2, index+2)
                pyxl_sheet = self.pyxl[sheet_name]
                cell = pyxl_sheet[str(cl)]
                logger.debug(cell)
                logger.debug(cell.value)
                name = headers[index].name
                required = headers[index].required
                sp = SpreadsheetProperty(name, value, cl, required)
                spreadsheet_rows.append(sp)
            else:
                sr = SpreadsheetRow(spreadsheet_rows, sheet_name)
                data.append(sr)

        return data


    def _parse_project(self): 
        tab_name = "project"
        nodes = {}
        def parse_project_node():
            startrow = self._seek(tab_name, "Project Information")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("project", data)
            return sn

        def parse_dataset_node():
            startrow = self._seek(tab_name, "Datasets")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("dataset", data)
            return sn

        def parse_external_dataset_node():
            startrow = self._seek(tab_name, "External Datasets")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("external_dataset", data)
            return sn

        def parse_contributors_node():
            startrow = self._seek(tab_name, "Contributors")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("contributor", data)
            return sn

        nodes["project"]          = parse_project_node()
        nodes["dataset"]          = parse_dataset_node()
        nodes["external_dataset"] = parse_external_dataset_node()
        nodes["contributor"]      = parse_contributors_node()
        return nodes


    def _parse_experiments_genomic(self):
        tab_name = "experiments_genomic"
        nodes = {}
        def parse_experiment_node():
            startrow = self._seek(tab_name, "Experiments")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("experiment", data)
            return sn
        def parse_genomic_node():
            startrow = self._seek(tab_name, "Genomes")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("genome", data)
            return sn

        #exp_nodes = parse_experiment_node()
        #print(f"exp_nodes: {exp_nodes}")
        nodes["experiment"] = parse_experiment_node()
        nodes["genome"]    = parse_genomic_node()
        return nodes


    def _parse_experiments_metagenomic(self):
        tab_name = "experiments_metagenomic"
        nodes = {}
        def parse_experiment_node():
            startrow = self._seek(tab_name, "Experiments")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("experiment", data)
            return sn
        def parse_metagenomic_node():
            startrow = self._seek(tab_name, "Metagenomes")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("metagenome", data)
            return sn
        nodes["experiment"] = parse_experiment_node()
        # append genomic experiments to metagenomic experiments
        #nodes["experiment"].update(parse_experiment_node())

        nodes["metagenome"] = parse_metagenomic_node()
        return nodes
    

    def _parse_samples(self):
        '''
        the only data on the samples tab are the samples themselves
        so the implementation is a bit simpler than the other tabs
        '''
        tab_name = "samples"
        nodes = {}
        def parse_sample_node():
            data = self._seek_data(tab_name, 0)
            sn = SpreadsheetNode("sample", data)
            return sn
        nodes["sample"] = parse_sample_node()
        return nodes


    def _parse_files_instruments(self):
        tab_name = "files_instruments"
        nodes = {}
        def parse_file_node():
            data = self._seek_data(tab_name, 0)
            sn = SpreadsheetNode("file", data)
            return sn
        def parse_instrument_node():
            '''
            this has been deprecated because file and instrument 
            metadata have been combined into a single table in the 
            AGDR metadata spreadsheet template
            '''
            startrow = self._seek(tab_name, "Instrument and sequencing metadata")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow)
            sn = SpreadsheetNode("instruments", data)
            return sn
        nodes["file"]       = parse_file_node()
        #nodes["instrument"] = parse_instrument_node()
        return nodes

    
    def _parse_nesi_internal_use(self):
        '''
        returns a version string

        it will be found in the first column of the sheet, and is 
        the last value listed before "Please do not modify this sheet"
        text is found
        '''
        tab_name = "NeSI_internal_use"
        # open the sheet
        sheet = pd.read_excel(self.pd_excel, tab_name)
        rows, _ = sheet.shape
        version_string = None

        skipped_empty_lines = False
        for r in range(rows):
            # if row is empty, skip
            if pd.isna(sheet.loc[r].iat[0]):
                if skipped_empty_lines:
                    return version_string
                else: continue
            else:
                skipped_empty_lines = True
            
            version_string = str(sheet.loc[r].iat[0]).strip()
        return version_string


    def _parse_tab(self, tab_name):
        if tab_name.lower() == "project":
            return self._parse_project()
        elif tab_name.lower() == "experiments_genomic":
            return self._parse_experiments_genomic()
        elif tab_name.lower() == "experiments_metagenomic":
            return self._parse_experiments_metagenomic()
        elif tab_name.lower() == "samples":
            return self._parse_samples()
        elif tab_name.lower() == "files_instruments":
            return self._parse_files_instruments()
        # the version gets in the constructor so that the version may be print
        # to the console before parsing
        elif tab_name.lower() == "nesi_internal_use":
            #self.version = self._parse_nesi_internal_use()
            return {}
        else:
            raise BadMetadataSpreadhsheetException("Tab not recognized")
        return {}


    def _open_excel_helper(self):
        book_path = self.datapath.split("/")[-1]
        extension = book_path.split(".")[-1]
        if not extension.lower() == "xlsx":
            raise Exception("File extension must be .xlsx")

    def _open_pyxl(self):
        self._open_excel_helper()
        return openpyxl.load_workbook(self.datapath)

    def _open_book(self):
        self._open_excel_helper()
        return pd.ExcelFile(self.datapath)


    def parse_old(self):
        with alive_bar(title="\tParsing AGDR spreadsheet", length=len(self.tabs)) as bar:
            for index, tabName in enumerate(self.tabs):
                logger.debug(f"tabName: {tabName}")
                logger.debug(f"index: {index}")
                self.nodes.update(self._parse_tab(tabName))
                bar()

    def parse(self):
        def update_nodes(parsed_data):
            for key in parsed_data:
                if key in self.nodes:
                    #print(f"pre: {self.nodes[key]}")
                    #print(f"____extending {key}")
                    # extend the list of SpreadsheetRow objects
                    self.nodes[key].update(parsed_data[key]) 
                    #print(f"post: {self.nodes[key]}")
                else:
                    #print(f"____updating  {key}")
                    # add the key-value pair to the dictionary
                    self.nodes[key] = parsed_data[key]
        with alive_bar(title="\tParsing AGDR spreadsheet", length=len(self.tabs)) as bar:
            for index, tabName in enumerate(self.tabs):
                logger.debug(f"tabName: {tabName}")
                logger.debug(f"index: {index}")
                #self.nodes.update(self._parse_tab(tabName))
                update_nodes(self._parse_tab(tabName))
                bar()

