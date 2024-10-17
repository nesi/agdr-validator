'''
@Author: Eirian Perkins

This file is a subclass of TSVTransformer, and is intended to convert
metadata from a spreadsheet aligned with the 2022-09-23 version of the
AGDR schema into a collection of TSV files, which can be then used 
for metadata ingestion into a Gen3 data commons.
'''
from agdrvalidator.transformer.tsv import TSVTransformer
from agdrvalidator.utils import logger

import datetime
import os

logger = logger.setUp(__name__)

empty_values = [
    None,
    "",
    "unknown",
    "not collected",
    "not provided",
    "not applicable",
    "not available",
    "not reported",
    "not specified",
    "none",
    "na",
    "nan"
]

class AGDRTSVTransformer(TSVTransformer):
    def __init__(self, node):
        super().__init__(node)

        # extract node type
        self.table_name = node.gen3_name
        # extract header from node
        self.headers = self._buildHeaderFromProps(node)
        # extract data from node
        #self.data = self._buildDataFromProps(node)
        self.data = []

    def _buildHeaderFromProps(self, node):
        headers = set()
        for property in node:
            if not property.gen3_name:
                continue
            col_name = property.gen3_name
            if property.required:
                col_name = "*" + col_name
            headers.add(col_name)
        logger.info(f"{node.gen3_name} headers: {list(headers)}")
        return list(headers)

    def _buildDataFromProps(self, node):
        pass

    #def convert(self):
    #    # convert self._node to tsv
    #    # return tsv
    #    pass

    def addRow(self, node):
        properties = node.data
        row_data = []
        for header in self.headers:
            column = header.strip("*")
            #if column == "type":
            #    continue
            property = node.getProperty(column)
            if property and property.get_value():
                row_data.append(property.get_value())
            else:
                row_data.append("")
        self.data.append(row_data)

    def _stripEmptyRows(self):
        empty_rows = [] # list of header names to be removed

        row0 = self.data[0]
        for idx, hdr in enumerate(self.headers):
            #print(f"checking header: {hdr}")
            if str(row0[idx]).lower().strip() in empty_values:
                # check if all rows are empty
                allEmpty = True
                for row in self.data[1:]:
                    if str(row[idx]).lower().strip() not in empty_values:
                        allEmpty = False
                else:
                    if allEmpty:
                        empty_rows.append(hdr)
                    else:
                        for row in self.data:
                            if str(row[idx]).lower().strip() in empty_values:
                                row[idx] = ""
        for hdr in empty_rows:
            idx = self.headers.index(hdr)
            for row in self.data:
                row.pop(idx)
            self.headers.remove(hdr)

    def toTSV(self, outputdir, nodecount=None):
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        # order from root to leaves
        outputfile = os.path.join(outputdir, str(nodecount) + self.table_name + ".tsv")
        #outputfile = os.path.join(outputdir, self.table_name + ".tsv")


        # strip out empty rows
        self._stripEmptyRows()

        with open (outputfile, 'w', encoding="utf-8") as f:
            f.write("\t".join(self.headers) + "\n")
            for row in self.data:
                # TODO: this will remove newlines in project descriptions
                # if an item's type is string, then put quotes around it
                # (would be the fix here), just use typof()
                f.write("\t".join([   " ".join(str(x).split("\n"))   for x in row]) + "\n")
