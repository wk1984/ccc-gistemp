#! /usr/bin/env python
# $URL$
# $Rev$
#
# read_config.py
#
# Nick Barnes, Ravenbrook Limited, 2010-01-16

"""
Python code to read the various config and station files used by
GISTEMP:
"""

def v2_get_sources():
    """Reads the three tables mcdw.tbl, ushcn2.tbl, sumofday.tbl and
    return a dictionary that maps from 12-digit (string) station ID to
    the source (which is one of the strings 'MCDW', 'USHCN2',
    'SUMOFDAY').
    """

    sources = {}
    for source in ['MCDW', 'USHCN2', 'SUMOFDAY']:
        for line in open('input/%s.tbl' % source.lower()):
            _, id, rec_no = line.split()
            sources[id + rec_no] = source
    return sources


def get_helena_dict():
    """Reads the file config/combine_pieces_helena.in into a dict,
    mapping a station id to a tuple (ID with duplicate marker, year,
    month, summand)."""

    helena_ds = {}
    for line in open('config/combine_pieces_helena.in', 'r'):
        id, _, year, month, summand = line.split()
        helena_ds[id] = (int(year), int(month), float(summand))
    return helena_ds


def get_changes_dict():
    """Reads the file config/Ts.strange.RSU.list.IN and returns a dict
    result.  Each line in that file begins with a 12-digit station ID
    - actually the tuple (country-code, WMO station, modifier,
    duplicate) - and ends with either yyyy/mm, specifying a month
    datum to omit or with xxxx-yyyy, specifying years to omit.  xxxx
    can be 0, meaning from the beginning. yyyy can be 9999, meaning to
    the end.  The dict is a map from ID to ('month',yyyy,mm) or
    ('years',xxxx,yyyy).
    """

    dict = {}
    for line in open('config/Ts.strange.RSU.list.IN', 'r'):
        split_line = line.split()
        id = split_line[0]
        try:
            year1, year2 = map(int, split_line[-1].split("-"))
            val = ("years", year1, year2)
        except ValueError:
            year, month = map(int, split_line[-1].split("/"))
            val = ("month", year, month)
        dict[id] = dict.get(id,[])
        dict[id].append(val)
    return dict


def get_alter_dict():
    """Reads the file config/Ts.discont.RS.alter.IN into a dict.  Each
    line has a 12 digit station ID, a month, a year, and a
    floating-point temperature delta.  The dict maps the ID to (month,
    year, delta).
    """

    dict = {}
    for line in open('config/Ts.discont.RS.alter.IN'):
        id, month, year, num = line.split()
        dict[id] = [int(month), int(year), float(num)]
    return dict
