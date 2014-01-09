#!/usr/bin/env python
"""
Grid Tables Extension for Python-Markdown
=========================================

Add parsing of grid tables to Python-Markdown. These differ from simple tables
in that they can contain multi-lined text and (in my opinion) are cleaner
looking than simpe tables. They were inspired by reStructuredText's grid table
syntax. This extension was loosely based on the 'table' extension for
Python-Markdown by Waylan Limberg.

An example of a grid table:

    +---------------+---------------+-----------------+
    | First Header  | Second Header | Third Header    |
    +===============+===============+=================+
    | A cell that   | A cell that spans multiple      |
    | spans         | columns.                        |
    | multiple rows +---------------+-----------------+
    |               | One, two cell | Red & blue cell |
    +---------------+---------------+-----------------+

This should be generated as (but colspans and rowspans may not work at the moment):

    <table>
        <thead>
            <tr>
                <td>First Header</td>
                <td>Second Header</td>
                <td>Third Header</td>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td rowspan="2">A cell that spans multiple rows</td>
                <td colspan="2">A cell that spans multiple columns</td>
            </tr>
            <tr>
                <td>One, two cell</td>
                <td>Red & blue cell</td>
            </tr>
        </tbody>
    </table>

Licensed under GPLv3 by [Alexander Abbott aka Smartboy](http://smartboyssite.net)

Links referenced during creation of this plugin:
https://gist.github.com/1855764
http://packages.python.org/Markdown/extensions/api.html
https://github.com/waylan/Python-Markdown/blob/master/markdown/extensions/tables.py
http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#grid-tables
http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/docutils/parsers/rst/tableparser.py?revision=7320&content-type=text%2Fplain
"""

import markdown
from markdown.util import etree
import re, string, pdb

class GridTableExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.parser.blockprocessors.add('grid-table',
                                      GridTableProcessor(md.parser),
                                      '<hashheader')

def makeExtension(configs={}):
    return GridTableExtension(configs=configs)

class GridTableCell(object):
    """
    A single cell in a grid table. A cell's boundaries are determined by a
    starting point in the top left (start_row and start_col), as well as a
    width and a height. It also has a colspan and rowspan count for cells that
    span multiple rows or columns.
    """
    def __init__(self, start_row, start_col, width=1, height=1, colspan=1,
                 rowspan=1, text=""):
        self.text = text
        self._start_row = max(0, start_row)
        self._start_col = max(0, start_col)
        self._width = max(1, width)
        self._height = max(1, height)
        self._colspan = max(1, colspan)
        self._rowspan = max(1, rowspan)
    
    def __str__(self):
        """
        For simplicity, the string representation is also the python code
        representation.
        """
        return self.__repr__()
    
    def __repr__(self):
        """
        This is the python representation of the cell. If ran with eval, the
        output from this function would create a duplicate instance of this
        class.
        """
        retval = "GridTableCell(start_row={}, start_col={}, width={}, "
        retval += "height={}, colspan={}, rowspan={}, text={})"
        return retval.format(repr(self._start_row), repr(self._start_col),
                             repr(self._width), repr(self._height),
                             repr(self._colspan), repr(self._rowspan),
                             repr(self.text))
    
    def __eq__(self, other):
        """
        Checks if another cell is equivalent to this one.
        """
        return (self.start_row == other.start_row and
                self.start_col == other.start_col and
                self.width == other.width and
                self.height == other.height and
                self.colspan == other.colspan and
                self.rowspan == other.rowspan)
    
    @property
    def start_row(self):
        """
        Returns the starting row for the cell.
        """
        return self._start_row
    
    @start_row.setter
    def start_row(self, value):
        """
        Sets the starting row of the cell to either 0 or the value passed in,
        depending on which is larger.
        """
        self._start_row = max(0, value)
    
    @property
    def start_col(self):
        """
        Returns the starting column for the cell.
        """
        return self._start_col
    
    @start_col.setter
    def start_col(self, value):
        """
        Sets the starting column of the cell to either 0 or the value passed
        in, depending on which is larger.
        """
        self._start_col = max(0, value)
    
    @property
    def width(self):
        """
        Returns the width (in number of characters) of the cell.
        """
        return self._width
    
    @width.setter
    def width(self, value):
        """
        Sets the width (in number of characters) of the cell to either 1 or the
        value passed in, depending on which is larger.
        """
        self._width = max(1, value)
    
    @property
    def height(self):
        """
        Returns the height (in number of characters) of the cell.
        """
        return self._height
    
    @height.setter
    def height(self, value):
        """
        Sets the height (in number of characters) of the cell to either 1 or
        the value passed in, depending on which is larger.
        """
        self._height = max(1, value)
    
    @property
    def colspan(self):
        """
        Returns the number of columns that this cell spans.
        """
        return self._colspan
    
    @colspan.setter
    def colspan(self, value):
        """
        Sets the number of columns that this cell spans to either 1 or the
        value passed in, depending on which is larger.
        """
        self._colspan = max(1, value)
    
    @property
    def rowspan(self):
        """
        Returns the number of rows that this cell spans.
        """
        return self._rowspan
    
    @rowspan.setter
    def rowspan(self, value):
        """
        Sets the number of rows that this cell spans to either 1 or the value
        passed in, depending on which is larger.
        """
        self._rowspan = max(1, value)
    
    @property
    def end_row(self):
        """
        Returns the index of which row the cell ends at within the block. This
        is changed by modifying either the starting row or the height of this
        cell.
        """
        return self._start_row + self._height
    
    @property
    def end_col(self):
        """
        Returns the index of which column the cell ends at within the block.
        This is changed by modifying either the starting column or the width of
        this cell.
        """
        return self._start_col + self._width

class GridTableRow(object):
    """
    A single row in a grid table, which can contain any number of cells. Cells
    within a row may not start at the same index as where the row starts, since
    they may span multiple columns.
    """
    def __init__(self, start_row, is_header=False):
        self._cells = []
        self._start_row = start_row
        self._height = None
        self.is_header = is_header
    
    def add_cell(self, cell):
        """
        Adds a cell to the appropriate position in the row based on where its
        left and right edges are. This returns false if a cell overlaps with
        another cell in the row, otherwise it returns true.
        """
        for i in range(0, len(self._cells)):
            if cell.start_col + cell.width <= self._cells[i].start_col:
                if i > 0 and not self._cells[i-1].start_col + self._cells[i-1].width <= cell.start_col:
                    return False
                self._cells.insert(i, cell)
                break
        else:
            if len(self._cells) > 0 and self._cells[-1].start_col + self._cells[-1].width > cell.start_col:
                return False
            self._cells.append(cell)
        relative_height = cell.start_row + cell.height - self._start_row
        if self._height is None or relative_height < self._height:
            self._height = relative_height
        return True
    
    def get_all_cells(self):
        """
        A generator which returns all cells within the row. I use a generator
        since I mainly use this in for loops, and it's more memory efficient
        and code efficient with a generator.
        """
        for cell in self._cells:
            yield cell
    
    def get_all_cells_taller_than_this_row(self):
        """
        A generator that gets all cells that are taller than this row (which
        means they span multiple rows).
        """
        for cell in self._cells:
            if cell.start_row + cell.height > self._start_row + self._height:
                yield cell
    
    def get_all_cells_starting_at_this_row(self):
        """
        A generator that gets all cells that start at this row (which means
        they are not spanning from another row).
        """
        for cell in self._cells:
            if cell.start_row == self._start_row:
                yield cell
    
    def get_cell_starting_at_this_row_at_column(self, column):
        """
        Returns the cell (or None if no cell is found) that starts in this row,
        at the column specified.
        """
        for cell in self.get_all_cells_starting_at_this_row():
            if cell.start_col == column:
                return cell
            elif cell.start_col > column:
                break
        return None
    
    @property
    def height(self):
        """
        Returns the height (in number of characters) of this row. The height is
        equal to the height of the shortest cell in this row.
        """
        return self._height
    
    @property
    def start_row(self):
        """
        The index of the line in the block at which this row starts.
        """
        return self._start_row
        
    @property
    def end_row(self):
        """
        The index of the line in the block at which this row ends. This is
        equal to the starting row plus the height.
        """
        return self._start_row + self._height
    
    @property
    def start_col(self):
        """
        The column in the block at which this row starts. If a cell starts at
        this row, that cell's start column is returned. Otherwise, the furthest
        right connected cell's (starting from the left) end column is returned.
        """
        if len(self._cells) == 0:
            return 0
        left_cell = None
        for cell in self._cells:
            if cell.start_row == self.start_row:
                return cell.start_col
            if left_cell is None or left_cell.end_col == cell.start_col:
                left_cell = cell
            else:
                break
        return left_cell.end_col
    
    @property
    def end_col(self):
        """
        Returns the ending column for this row. The ending column is equal to
        the last cell's ending column.
        """
        if len(self._cells) == 0:
            return 0
        return self._cells[-1].end_col

class GridTable(object):
    """
    A grid table in its entirity. The start row and start column should be 0, 0
    but can be set differently depending on the block. The width and height are
    how many characters wide and high the table is.
    """
    def __init__(self, start_row, start_col, height, width, first_row_header=False):
        self._rows = [GridTableRow(start_row, is_header=first_row_header)]
        self._start_row = start_row
        self._start_col = start_col
        self._width = width
        self._height = height
    
    def new_row(self, is_header=False, header_location=-1):
        """
        Creates a new row which starts at the end of the previous row. Any
        cells that are larger than the height of this row are added to the new
        row.
        """
        self._rows.append(GridTableRow(self._rows[-1].end_row, is_header))
        for cell in self._rows[-2].get_all_cells_taller_than_this_row():
            cell.rowspan += 1
            self._rows[-1].add_cell(cell)
        return self._rows[-1].start_row, self._rows[-1].start_col
    
    def add_cell(self, cell):
        """
        Adds a cell to the last row in the table.
        """
        return self._rows[-1].add_cell(cell)
    
    def get_all_rows(self):
        """
        A generator that returns all rows in the table.
        """
        for row in self._rows:
            yield row
    
    def get_all_cells_starting_at_column(self, column):
        """
        A generator which yields all cells in all rows that start at a specific
        column.
        """
        for row in self._rows:
            cell = row.get_cell_starting_at_this_row_at_column(column)
            if cell is not None:
                yield cell
    
    def calculate_colspans(self):
        """
        After all cells are added to the table, this function will calculate
        all colspans for all cells in the array. It does this by walking
        through all cells and finding each column in which a cell ends, and
        increasing the colspans of all rows that start before that column and
        ends after that column by one.
        """
        start_col = self._start_col
        end_col = self.end_col
        cells = []
        while start_col < end_col:
            new_cells = list(self.get_all_cells_starting_at_column(start_col))
            for cell in new_cells:
                if cell not in cells:
                    cells.append(cell)
            for cell in cells:
                if cell.end_col < end_col:
                    end_col = cell.end_col
            for i in range(len(cells)-1, -1, -1):
                if cells[i].end_col > end_col:
                    cells[i].colspan += 1
                else:
                    del cells[i]
            start_col = end_col
            end_col = self.end_col
    
    @property
    def start_row(self):
        """
        Returns the index of the row (in number of characters) that the table
        starts at.
        """
        return self._start_row
    
    @property
    def start_col(self):
        """
        Returns the index of the column (in number of characters) that the
        table starts at.
        """
        return self._start_col
    
    @property
    def width(self):
        """
        Returns the width (in number of characters) of the table.
        """
        return self._width
    
    @property
    def height(self):
        """
        Returns the height (in number of characters) of the table.
        """
        return self._height
    
    @property
    def end_row(self):
        """
        Returns the index of the row (in number of characters) that the table
        ends at. It is equal to the starting row plus the height.
        """
        return self._start_row + self._height
    
    @property
    def end_col(self):
        """
        Returns the index of the column (in number of characters) that the
        table ends at. It is equal to the starting row plus the height.
        """
        return self._start_col + self._width

    @property
    def has_header(self):
        return self._rows[0].is_header

class GridTableProcessor(markdown.blockprocessors.BlockProcessor):
    """
    The markdown block processor used to parse a grid table. A malformed grid
    table is generated as a block of text instead of being removed.
    """
    _header_regex = r'\+=+(\+=+)*\+'

    def test(self, parent, block):
        """
        This function tests to see if the block of text passed in is a table or
        not. A table is thus defined as a block of text which has more than 2
        lines, has a '+-' on both the top and bottom left corners, has a '-+'
        on both the top an bottom right corners, and has a '|' at the beginning
        and end of the first and last rows.
        """
        rows = [r.strip() for r in block.split('\n')]
        return (len(rows) > 2 and rows[0][:2] == "+-" and rows[0][-2:] == "-+"
                and rows[1][0] == '|' and rows[1][-1] == '|'
                and rows[-2][0] == '|' and rows[-2][-1] == '|'
                and rows[-1][:2] == "+-" and rows[-1][-2:] == "-+")

    def run(self, parent, blocks):
        """
        Starts parsing the block of text which contains the table. It first
        finds the header (if one exists) as ended by a row of '=' characters.
        It then gets all the cells in the body (as a separate table from the
        header; this needs to be changed). If getting either the header or the
        body fails, the table is instead rendered as a block of text.
        Otherwise, it is rendered as a table with the appropriate row and
        column spans.
        """
        orig_block = [r.strip() for r in blocks.pop(0).split('\n')]
        body_block = orig_block[:]
        success, body = self._get_all_cells(body_block)
        if not success:
            self._render_as_block(parent, '\n'.join(orig_block))
            return
        table = etree.SubElement(parent, 'table')
        self._render_rows(body, table)

    def _render_as_block(self, parent, text):
        """
        Renders a table as a block of text instead of a table. This isn't done
        correctly, since the serialized items are serialized again, but I'll
        fix this later.
        """
        trans_table = [(' ', '&nbsp;'), ('<', '&lt;'), ('>', '&gt;'), ('&', '&amp;')]
        for from_char, to_char in trans_table:
            text = text.replace(from_char, to_char)
        div = etree.SubElement(parent, 'div')
        div.set('class', 'grid-table-error')
        div.text = text

    def _header_exists(self, block):
        """
        Checks if a header exists. A header is defined by a row of '='
        characters.
        """
        for row, i in zip(block, range(0, len(block))):
            if re.match(self._header_regex, row):
                return True, i, self._get_header(block)
        return False, -1, block

    def _get_header(self, block):
        """
        Separates the header of the table from the body, putting them both into
        their own separate blocks and replacing the header separator with a
        normal separator.
        """
        block = block[:]
        for i in range(0, len(block)):
            if re.match(self._header_regex, block[i]):
                block[i] = block[i].replace('=', '-')
                break
        return block

    def _render_rows(self, table, parent):
        """
        Renders all rows in a table into 'tr' elements, and all cells into all
        'td' elements.
        """
        header_cell_tag = 'th'
        body_cell_tag = 'td'
        rendered = []
        if table.has_header:
            header_subparent = etree.SubElement(parent, 'thead')
            body_subparent = etree.SubElement(parent, 'tbody')
        else:
            header_subparent = body_subparent = etree.SubElement(parent, 'tbody')
        for row in table.get_all_rows():
            if table.has_header and row.is_header:
                subparent = header_subparent
            else:
                subparent = body_subparent
            if len(list(row.get_all_cells())) != 0:
                tr = etree.SubElement(subparent, 'tr')
            for cell in row.get_all_cells():
                if not cell in rendered:
                    if row.is_header:
                        cell_element = etree.SubElement(tr, header_cell_tag)
                    else:
                        cell_element = etree.SubElement(tr, body_cell_tag)
                    rendered.append(cell)
                    self.parser.parseBlocks(cell_element, cell.text.split('\n\n'))
                    cell_element.set('rowspan', str(cell.rowspan))
                    cell_element.set('colspan', str(cell.colspan))
    
    def _get_all_cells(self, block):
        """
        Finds all cells within the block and assembles them into a table
        object. Not all rows in this table will have the same length due to
        the possibility that cells span multiple rows. Returns the success or
        failure of finding all cells and the table object itself. If this
        fails, that means that the input was malformed.
        """
        start_row = start_col = 0
        header_exists, header_location, block = self._header_exists(block)
        table = GridTable(start_row, start_col, len(block)-1, len(block[0])-1, header_exists)
        while start_row < len(block)-1:
            new_cell = self._scan_cell(block, start_row, start_col)
            if new_cell is None or not table.add_cell(new_cell):
                return False, table
            if start_col + new_cell.width >= len(block[start_row])-1:
                is_header = header_exists and table._rows[-1].end_row < header_location
                start_row, start_col = table.new_row(is_header=is_header)
            else:
                start_col += new_cell.width
        table.calculate_colspans()
        return True, table
    
    def _scan_cell(self, block, start_row, start_col):
        """
        Starts scanning for a specific cell by checking the starting character
        to make sure it's valid. It scans in the order right, down, left, up
        to see if it can get back to its starting position. If it can, a new
        GridTableCell is returned, and if it can't, None is returned.
        """
        if block[start_row][start_col] != '+':
            return None
        return self._scan_right(block, start_row, start_col)
    
    def _scan_right(self, block, start_row, start_col):
        """
        Scans right until it gets to a '+' sign. It then starts scanning down
        to see if it can find a complete path, if it can't, it continues
        scanning right. Otherwise, it returns the cell it found.
        """
        width = 1
        while start_col + width < len(block[start_row]):
            cur_col = start_col + width
            if block[start_row][cur_col] == '+':
                result = self._scan_down(block, start_row, start_col, cur_col)
                if result is None:
                    width += 1
                    continue
                return result
            elif block[start_row][cur_col] == '-':
                width += 1
            else:
                break
        return None
    
    def _scan_down(self, block, start_row, start_col, cur_col):
        """
        Scans down until it gets to a '+' sign. It then starts scanning left
        to see if it can find a complete path back to the starting position.
        If it can, then it returns the cell it found, otherwise, it returns
        None.
        """
        height = 1
        while start_row + height < len(block):
            cur_row = start_row + height
            if block[cur_row][cur_col] == '+':
                result = self._scan_left(block, start_row, start_col, cur_col, cur_row)
                if result is None:
                    height += 1
                    continue
                return result
            elif block[cur_row][cur_col] == '|':
                height += 1
            else:
                break
        return None
    
    def _scan_left(self, block, start_row, start_col, cur_col, cur_row):
        """
        Scans left until it gets to a '+' sign. It then starts scanning up to
        verify that the path found is a complete cell and that it gets back to
        the starting position. If it does, it returns the cel. Otherwise it
        returns None.
        """
        width = 1
        while cur_col - width >= 0:
            check_col = cur_col - width
            if block[cur_row][check_col] == '+':
                result = self._scan_up(block, start_row, start_col, cur_col, cur_row, check_col)
                if result is None:
                    width += 1
                    continue
                return result
            elif block[cur_row][check_col] == '-':
                width += 1
            else:
                break
        return None
    
    def _scan_up(self, block, start_row, start_col, cur_col, cur_row, check_col):
        """
        Scans up until it gets to a '+' sign. If the '+' sign is in the
        starting position, it returns a new GridTableCell. Otherwise, it
        scans right again to verify it doesn't connect to any new paths and
        create a new cell. If it does, then it returns None, since its
        malformed. Otherwise it continues scanning up.
        """
        height = 1
        while cur_row - height >= 0:
            check_row = cur_row - height
            if block[check_row][check_col] == '+':
                if start_row == check_row and start_col == check_col:
                    cell = GridTableCell(start_row, start_col, cur_col - start_col, height)
                    cell.text = self._gather_text(block, cell.start_row, cell.start_col, cell.end_row, cell.end_col)
                    return cell
                result = self._scan_right(block, check_row, check_col)
                if result is not None:
                    return None
                height += 1
                continue
            elif block[check_row][check_col] == '|':
                height += 1
            else:
                break
        return None
    
    def _gather_text(self, block, start_row, start_col, end_row, end_col):
        """
        Gathers the text within the cell defined by the start row, start
        column, end row, and end column and returns them as one string.
        """
        text = []
        for i in range(start_row+1, end_row):
            text.append(block[i][start_col+1:end_col].rstrip())
        return '\n'.join(self._unindent_one_level(text))
    
    def _unindent_one_level(self, text):
        """
        Unindents the text one level, up to the index of the farthest-left
        non-blank character in the text.
        """
        chars = 0
        for i in range(0, len(max(text, key=len))):
            for line in text:
                if i < len(line) and line[i] != ' ':
                    break
            else:
                chars += 1
                continue # This skips the break below
            break
        for i in range(0, len(text)):
            text[i] = text[i][chars:]
        return text
