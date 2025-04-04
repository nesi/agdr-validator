'''
The purpose of this file is to parse AGDR spreadsheets. The spreadsheet 
templates are currently versioned. This file is for the 2024-08-28 version 
of the AGDR metadata template, which corresponds to the 2024-09-10 version 
of the AGDR metadata dictionary.
'''
import datetime
import sys

import openpyxl
import pandas as pd
from alive_progress import alive_bar

from agdrvalidator import AgdrFormatException, BadMetadataSpreadsheetException
from agdrvalidator.parser import *
from agdrvalidator.schema.agdrspreadsheet_validator import \
    AGDRSpreadsheetValidator
from agdrvalidator.utils import logger
from agdrvalidator.utils.array import *
from agdrvalidator.utils.rich_tabular import *

logger = logger.setUp(__name__)


class Agdr(Parser):
    def __init__(self, datapath, project):
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
        self.asv = AGDRSpreadsheetValidator()
        self.spreadsheet_report_output = f"{project}_spreadsheet_validation_report_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"


    def _seek(self, sheet_name, text):
        '''
        helper method for finding a "table" within a sheet, like 
        Project Information, Dataset, Contributors, etc.
        '''
        # in the first column, find the row with the text
        # want to return row number, so the callee knows
        # where to start parsing
        try:
            sheet = pd.read_excel(self.pd_excel, sheet_name)
            rows, _ = sheet.shape
            for r in range(rows):
                cell_text = str(sheet.loc[r].iat[0]).strip()
                if cell_text.lower() == text.lower():
                    return r
            else:
                e = f"Could not find {text} in sheet"
                raise BadMetadataSpreadsheetException(e)
        except Exception as e:
            print(f"An error occurred while analysis the spreadsheet: {e} {sheet_name}. Please make sure that no sections are deleted from the original template even if unused and that they have not been renamed.")
            sys.exit(1)

    def _seek_fields(self, sheet_name, startrow) -> SpreadsheetRow:
        '''
        helper node for extracting "headers" from a "table" like 
        Project Information or Dataset

        should only be called by self._seek_data()

        must return a SpreadsheetRow object
        '''
        try:
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
                raise BadMetadataSpreadsheetException(e)

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
        except Exception as e:
            print(f"An error occurred while analysis the spreadsheet: {e} {sheet_name}. Please make sure that no sections are deleted from the original template even if unused and that they have not been renamed.")
            sys.exit(1)

    def _seek_data(self, sheet_name, startrow, node_name):
        '''
        helper method for extracting data for a particular node
        '''
        try:
            sheet = pd.read_excel(self.pd_excel, sheet_name)
            headers = self._seek_fields(sheet_name, startrow)
            self.asv.add(node_name, headers)
            self.headers = headers
            sections_mapping = {
                "raw",
                "sample",
                "experiment"
            }
            rows, _ = sheet.shape
            text = "Your input"
            text2 = "Example input"
            data = []
            datastart = None
            for r in range(startrow, rows):
                cell_text = str(sheet.loc[r].iat[0]).strip()
                if cell_text.lower() == text.lower():
                    datastart = r
                    if r - 1 > 0:
                        cell_text2 = str(sheet.loc[r-1].iat[0]).strip()
                        if cell_text2.lower() != text2.lower():
                            print(f"**************WARNING************ \n"
                                  f"Please make sure that \"{text}\" is on at least the first row of a table that needs to be ingested in {sheet_name} tab "
                                  f"otherwise rows will be missed \n"
                                  f"**************WARNING************ \n")
                    if node_name in sections_mapping and r > 10:
                        print(f"**************WARNING************ \n"
                            f"Please make sure that \"{text}\" is on at least the first row of a table {node_name} that needs to be ingested in {sheet_name} tab "
                            f"otherwise rows will be missed \n"
                            f"**************WARNING************ \n")
                    break
            else:
                if datastart == None:
                    e = f"Could not find {text} in sheet"
                    raise BadMetadataSpreadsheetException(e)

            # now extract all rows of data until the row is empty
            for r in range(datastart, rows):
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
        except Exception as e:
            print(f"An error occurred while analysis the spreadsheet: {e} {sheet_name}. Please make sure that no sections are deleted from the original template even if unused and that they have not been renamed.. Around row {startrow}.")
            sys.exit(1)


    def _parse_project(self): 
        tab_name = "project"
        nodes = {}
        def parse_project_node():
            startrow = self._seek(tab_name, "Project Information")
            data = self._seek_data(tab_name, startrow, "project")
            sn = SpreadsheetNode("project", data)
            return sn

        def parse_dataset_node():
            startrow = self._seek(tab_name, "Datasets")
            data = self._seek_data(tab_name, startrow, "dataset")
            sn = SpreadsheetNode("dataset", data)
            return sn

        def parse_external_dataset_node():
            startrow = self._seek(tab_name, "External Datasets")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow, "external_dataset")
            sn = SpreadsheetNode("external_dataset", data)
            return sn

        def parse_contributors_node():
            startrow = self._seek(tab_name, "Contributors")
            data = self._seek_data(tab_name, startrow, "contributors")
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
            data = self._seek_data(tab_name, startrow, "experiment")
            sn = SpreadsheetNode("experiment", data)
            return sn
        
        def parse_genomic_node():
            startrow = self._seek(tab_name, "Genomes")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow, "genome")
            sn = SpreadsheetNode("genome", data)
            return sn

        nodes["experiment"] = parse_experiment_node()
        nodes["genome"]    = parse_genomic_node()
        return nodes

    def _parse_experiments_metagenomic(self):
        tab_name = "experiments_metagenomic"
        nodes = {}
        def parse_experiment_node():
            startrow = self._seek(tab_name, "Experiments")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow, "experiment")
            sn = SpreadsheetNode("experiment", data)
            return sn
        
        def parse_metagenomic_node():
            startrow = self._seek(tab_name, "Metagenomes")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow, "metagenome")
            sn = SpreadsheetNode("metagenome", data)
            return sn
        nodes["experiment"] = parse_experiment_node()
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
            data = self._seek_data(tab_name, 0, "sample")
            sn = SpreadsheetNode("sample", data)
            return sn
        nodes["sample"] = parse_sample_node()
        return nodes

    def _parse_files_instruments(self):
        tab_name = "files_instruments"
        nodes = {}
        
        def parse_file_node():
            data = self._seek_data(tab_name, 0, "raw")
            sn = SpreadsheetNode("file", data)
            return sn
        
        def parse_files_supplementary():
            startrow = self._seek(tab_name, "Supplementary file metadata")
            logger.debug(f"startrow: {startrow}")
            data = self._seek_data(tab_name, startrow, "supplementary_file")
            sn = SpreadsheetNode("supplementary_file", data)
            return sn
        
        nodes["file"]               = parse_file_node()
        nodes["supplementary_file"] = parse_files_supplementary()
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
        if str(tab_name).lower() == "project":
            return self._parse_project()
        elif str(tab_name).lower() == "experiments_genomic":
            return self._parse_experiments_genomic()
        elif str(tab_name).lower() == "experiments_metagenomic":
            return self._parse_experiments_metagenomic()
        elif str(tab_name).lower() == "samples":
            return self._parse_samples()
        elif str(tab_name).lower() == "files_instruments":
            return self._parse_files_instruments()
        elif str(tab_name).lower() == "nesi_internal_use":
            return {}
        else:
            raise BadMetadataSpreadsheetException("Tab not recognized")
        return {}

    def _open_excel_helper(self):
        book_path = self.datapath.split("/")[-1]
        extension = book_path.split(".")[-1]
        if not str(extension).lower() == "xlsx":
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
                    # extend the list of SpreadsheetRow objects
                    self.nodes[key].update(parsed_data[key]) 
                else:
                    # add the key-value pair to the dictionary
                    self.nodes[key] = parsed_data[key]
        with alive_bar(title="\tParsing AGDR spreadsheet", length=len(self.tabs)) as bar:
            for index, tabName in enumerate(self.tabs):
                logger.debug(f"tabName: {tabName}")
                logger.debug(f"index: {index}")
                update_nodes(self._parse_tab(tabName))
                bar()
        self.asv.validate(self.spreadsheet_report_output)

