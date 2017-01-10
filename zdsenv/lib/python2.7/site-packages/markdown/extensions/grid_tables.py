#!/usr/bin/env python

import markdown
from markdown.util import etree
from markdown.blockprocessors import BlockProcessor
import re
from functools import reduce
from itertools import chain, tee, repeat
from collections import namedtuple


##################################
# Python-ZMarkdown Extension API #
##################################


class GridTableExtension(markdown.Extension):
    """
    Add Grid-Table support.
    """

    def extendMarkdown(self, md, md_globals):
        md.parser.blockprocessors.add('grid-table',
                                      GridTableProcessor(md.parser),
                                      '<hashheader')


class GridTableProcessor(BlockProcessor):
    def test(self, parent, block):
        return bool(extract_table_line_of(block))

    def run(self, parent, blocks):

        # Extract tables lines of first block
        m = extract_table_line_of(blocks.pop(0))
        if not m:  # pragma: no cover
            # Should not happen
            return False
        lines, rest, has_header = m

        # Compute columns starting positions
        lines_info = compute_columns_starting_positions(lines)

        # We will generate a table

        table_content = extract_table_content(lines, lines_info, has_header)
        generate_table(self.parser, table_content, parent)

        # If remaining lines, process it
        if rest:
            blocks.insert(0, "\n".join(rest))


def makeExtension(*args, **kwargs):
    return GridTableExtension(*args, **kwargs)


###############################
# Generic utilities functions #
###############################


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ...
    From itertools documentation
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def find_all(txt, char):
    """Extract all position of a character in a string"""
    return tuple(i for i, ltr in enumerate(txt) if ltr in char)


def is_first_item():
    """A iterator that return True and then always False"""
    return chain([True], repeat(False))


###########################
# Lines testing functions #
###########################


# RE of line part. Ex: "+----+---+-------+"
line_part = r'\+\-[-+]+\-\+'
RE_line_part = re.compile(line_part)
# REfor a plain line (like line part but match the full line)
RE_line_plain = re.compile(r'^{}$'.format(line_part))
# RE of header part. Ex: "+====+===+=======+"
RE_line_header = re.compile(r'^\+=[=+]+=\+$')
# RE of main line (all others)
RE_line_main = re.compile(r'^((\+)|(\|)).+((\|)|(\+))$')


def is_plain_line(line):
    """Test if provided line is a plain line"""
    return bool(RE_line_plain.match(line))


def is_header_line(line):
    """Test if provided line is a header line"""
    return bool(RE_line_header.match(line))


def is_main_line(line):
    """Test if provided line is a main line"""
    return bool(RE_line_main.match(line))


def has_plain_line_part(line):
    """Test if provided line contain part of plain line"""
    return bool(RE_line_part.search(line))


def extract_table_line_of(block):
    """Extract all lines from a block or ``None`` if it is not a table.

    Return values : lines of table, rest of the content and if the table is an header.
    """

    # Speedy catcher : a block must start with "+-"
    if not block.startswith("+-"):
        return None

    # At least 3 lines required
    lines = block.split('\n')
    if len(lines) < 3:
        return None

    # Check first line
    if not is_plain_line(lines[0]):
        return None

    # Extract all table lines
    content = [lines[0]]
    has_header = False
    line_length = len(lines[0])

    for line in lines[1:]:
        # All lines must have the same length
        if len(line) != line_length:
            break

        # There can have only one header
        is_header = is_header_line(line)
        if has_header and is_header:
            break
        has_header = has_header or is_header

        # If it like a table line, add it
        if is_header or is_main_line(line):
            content.append(line)
        else:
            break

    # Last line should be a plain line
    while len(content) > 0:
        if not is_plain_line(content[-1]):
            content.pop()
        else:
            break

    # At least 3 lines required
    if len(content) < 3:
        return None

    return content, lines[len(content):], has_header


########################################
# Columns starting position extraction #
########################################


def compute_columns_starting_positions(lines):
    """Compute starting position of each columns of the table (=index position)"""

    lines_info = []
    stack_lines = []
    # Stack all main lines and compute their position at once.
    for line in lines:
        if is_header_line(line) or has_plain_line_part(line):
            if len(stack_lines) > 0:
                lines_info.append(compute_main_lines_columns_starting_positions(stack_lines))
                stack_lines = []
            lines_info.append(compute_plain_line_columns_starting_positions(line))
        else:
            stack_lines.append(line)

    ret = merge_columns_starting_positions(lines_info)
    return ret


def compute_plain_line_columns_starting_positions(line):
    """Extract all starting columns position in line with plain line part"""
    return find_all(line, '+|')


def compute_main_lines_columns_starting_positions(lines):
    """Extract all starting columns position in main lines"""
    column_info = (find_all(line, '|') for line in lines)
    return merge_columns_starting_positions(column_info, strict=False)


def merge_columns_starting_positions(starting_positions, strict=True):
    """merging all lines starting positions"""
    starting_positions = tuple(set(starting_positions))

    # If only one is provided, or all equals, return it
    if len(starting_positions) == 1:
        return starting_positions[0]
    # If more than two lines, reduce by merging it two-by-two
    elif len(starting_positions) > 2:
        return reduce(lambda e1, e2: merge_columns_starting_positions((e1, e2), strict=strict), starting_positions)
    # In strict mode, all starting position are keep
    elif strict:
        return tuple(sorted(set(chain.from_iterable(starting_positions))))
    # In non-strict mode, keep only position that match (bigger ones)
    else:
        return tuple(sorted(set(starting_positions[0]) & set(starting_positions[1])))


####################
# Table generation #
####################


# Table constructor : A small pseudo-ast class hierarchy helping create tables.

class TableContent(object):
    """Table content is the root object. Contains parts. There should have one or two part (header and main content)"""

    def __init__(self, lines_info):
        self.parts = []
        self.lines_info = lines_info
        self.add_part()

    def add_part(self):
        self.parts.append(TablePart(self.lines_info))

    def __iter__(self):
        return iter(self.parts)

    @property
    def last_part(self):
        return self.parts[-1]

    @property
    def raw_content(self):
        return [part.raw_content for part in self]


class TablePart(object):
    """Table part. Contains rows. There can have 1+ rows. Root logic : have the two mains update functions."""

    def __init__(self, lines_info):
        self.rows = []
        self.lines_info = lines_info
        self.add_row()

    def add_row(self):
        self.rows.append(TableRow(self.lines_info))

    def remove_last_row(self):
        self.rows.pop()

    @property
    def last_row(self):
        return self.rows[-1]

    def __iter__(self):
        return iter(self.rows)

    def update_with_main_line(self, line, is_end_line):
        """Main update function : update last row according to a line. If char at column limits are not authorized one,
        merge the two columns"""

        merge_chars = "+|" if is_end_line else "|"

        new_cells = [self.last_row.cells[0]]
        for cell in self.last_row.cells[1:]:
            # Only cells with rowspan equals can be merged
            if cell.rowspan == new_cells[-1].rowspan and line[cell.start_position - 1] not in merge_chars:
                new_cells[-1].merge_with(cell)
            else:
                new_cells.append(cell)
        self.last_row.cells = new_cells

    def update_with_part_line(self, line):
        """Update rows with line part : update rowspan by merging rows"""
        remaining_cells = []

        for cell in self.last_row:
            part_line = line[cell.start_position - 1:cell.end_position + 1]
            # All limitation that did not match plain line need to be merged, keep it for next row
            if not is_plain_line(part_line):
                cell.lines.append(line[cell.start_position:cell.end_position])
                cell.rowspan += 1
                remaining_cells.append(cell)
        # Add row and keep the previous cells witch need to be merged
        self.add_row()
        for remaining_cell in remaining_cells:
            self.last_row.cells = list(chain(
                [cell for cell in self.last_row if cell.end_position < remaining_cell.start_position],
                [remaining_cell],
                [cell for cell in self.last_row if cell.start_position > remaining_cell.end_position]))

    @property
    def raw_content(self):
        # Keep cells only in row where it first happen
        previous_row = []
        content = []
        for new_row in (row.raw_content for row in self):
            content.append([c for c in new_row if id(c) not in previous_row])
            previous_row = [id(c) for c in new_row]
        return content


class TableRow(object):
    """Table row : contain cells"""

    def __init__(self, lines_info):
        self.lines_info = lines_info
        self.cells = [TableCell(i1 + 1, i2) for i1, i2 in pairwise(lines_info)]

    def update_content(self, line):
        for cell in self:
            cell.lines.append(line[cell.start_position:cell.end_position])

    def __iter__(self):
        return iter(self.cells)

    @property
    def raw_content(self):
        return [cell.raw_content for cell in self]


class TableCell(object):
    """Table cells : contain lines of text"""

    def __init__(self, start_position, end_position):
        self.start_position = start_position
        self.end_position = end_position
        self.colspan = 1
        self.rowspan = 1
        self.lines = []
        self._rc = None

    def merge_with(self, other):
        self.end_position = other.end_position
        self.colspan += other.colspan
        self.lines = ["{}|{}".format(l1, l2) for l1, l2 in zip(self.lines, other.lines)]

    @property
    def raw_content(self):
        if self._rc is None:
            self._rc = RawCell("\n".join(l.strip() for l in self.lines), self.colspan, self.rowspan)
        return self._rc


# Describe a table cell
RawCell = namedtuple('Cell', 'content colspan rowspan')


def extract_table_content(lines, lines_info, has_header):
    """Extract table content : return raw table content with colspan/rowspan information for each cells."""
    # Create a table constructor
    table = TableContent(lines_info)

    for is_first_line, line in zip(is_first_item(), lines):
        # Check line type
        match_header = has_header and is_header_line(line)
        is_end_line = match_header or has_plain_line_part(line)

        if is_end_line:
            # It is a header, a plain line or a line with plain line part.

            # First update with main line to update last row according to new line separation
            table.last_part.update_with_main_line(line, is_end_line)

            # Update table part (will always create a new row)
            if not is_first_line:
                if match_header:
                    table.add_part()
                elif is_plain_line(line):
                    table.last_part.add_row()
                else:
                    table.last_part.update_with_part_line(line)

            # New raw lines are always created with global line information, need to be update
            table.last_part.update_with_main_line(line, is_end_line)

        else:
            # It is a plain line, update current row and add line content.
            table.last_part.update_with_main_line(line, is_end_line)
            table.last_part.last_row.update_content(line)

    # Table always end with a plain line, need to remove the last one
    table.last_part.remove_last_row()

    # Return a raw cleaned content
    return table.raw_content


def generate_table(parser, table_content, parent):
    """Generate table html element from extracted table content"""
    pr = etree.SubElement(parent, 'div')
    pr.set('class', "table-wrapper")
    table = etree.SubElement(pr, 'table')

    has_header = len(table_content) > 1

    for i, part in enumerate(table_content):
        if has_header and i == 0:
            root = etree.SubElement(table, 'thead')
        else:
            root = etree.SubElement(table, 'tbody')
        for row in part:
            tr = etree.SubElement(root, 'tr')
            for content, colspan, rowspan in row:
                td = etree.SubElement(tr, 'th' if has_header and i == 0 else 'td')
                td.set('rowspan', str(rowspan))
                td.set('colspan', str(colspan))
                parser.parseBlocks(td, content.split('\n\n'))

    return pr
