# coding: utf-8
from zds.settings import ZDS_APP

def paginator_range(current, stop, start=1):
    assert(current <= stop)

    # Basic case when no folding
    if stop - start <= ZDS_APP['paginator']['folding_limit']:
        return range(start, stop + 1)

    # Complex case when folding
    lst = []
    for page_number in range(start, stop + 1):
        # Bounds
        if page_number == start or page_number == stop:
            lst.append(page_number)
            if page_number == start and current - start > 2:
                lst.append(None)
        # Neighbors
        elif abs(page_number - current) == 1:
            lst.append(page_number)
            if page_number - current > 0 and stop - page_number > 2:
                lst.append(None)
        # Current
        elif page_number == current:
            lst.append(page_number)
        # Put some
        elif page_number == stop - 1 and current == stop - 3:
            lst.append(page_number)
        # And ignore all other numbers

    return lst
