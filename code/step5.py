#!/usr/bin/env python
# $URL$
# $Rev$
# 
# step5.py
#
# David Jones, Ravenbrook Limited, 2009-10-27

"""
STEP5 of the GISTEMP algorithm.

In STEP5: 8000 subboxes are combined into 80 boxes, and ocean data is
combined with land data; boxes are combined into latitudinal zones
(including hemispheric and global zones); annual and seasonal anomalies
are computed from monthly anomalies.
"""

# Clear Climate Code
import eqarea
# Clear Climate Code
import fort
# Clear Climate Code

# http://www.python.org/doc/2.3.5/lib/itertools-functions.html
import itertools
# http://www.python.org/doc/2.3.5/lib/module-math.html
import math
# http://www.python.org/doc/2.3.5/lib/module-struct.html
import struct
# http://www.python.org/doc/2.4.4/lib/module-os.html
import os


# See SBBXotoBX.f
def SBBXtoBX(land, ocean, box, log, rland, intrp, base=(1961,1991),
        ignore_land=False):
    """Simultaneously combine the land series and the ocean series and
    combine subboxes into boxes.  *land* and *ocean* should be open
    binary files for the land and ocean series (subbox gridded); *box*
    should be an open binary output file (where the output from this
    routine will be written); *log* should be an open text file (where
    diagnostic information will be logged); *rland* and *intrp* are
    equivalent to the command line arguments to SBBXotoBX.f.
    """
    
    landsubbox = iter(land)
    oceansubbox = iter(ocean)
    land_meta = landsubbox.next()
    ocean_meta = oceansubbox.next()

    bos ='>'
    boxf = fort.File(box, bos=bos)

    # RCRIT in SBXotoBX.f line 70
    # We make rland (and radius) a float so that any calculations done
    # using it are in floating point.
    radius = float(1200)
    if not ignore_land:
        rland = min(rland, radius)
    else:
        rland = -9999.0 # Actually this will not be used!
    # clamp intrp to [0,1]
    intrp = max(min(intrp, 1), 0)

    # Danger! Suspiciously similar to step3.py (because it's pasted):

    # number of boxes
    nbox = 80
    # number of subboxes within each box
    nsubbox = 100

    # Much of the Fortran code assumes that various "parameters" have
    # particular fixed values (probably accidentally).  I don't trust the
    # Python code to avoid similar assumptions.  So assert the
    # "parameter" values here.  Just in case anyone tries changing them.
    # Note to people reading comment becuse the assert fired:  Please
    # don't assume that the code will "just work" when you change one of
    # the parameter values.  It's supposed to, but it might not.
    assert nbox == 80
    # NCM in the Fortran
    assert nsubbox == 100

    # area of subbox in squared kilometres
    # Recall area of sphere is 4*pi*(r**2)
    # TOMETR in SBBXotoBX.f line 99
    import earth
    km2persubbox = (4*math.pi*earth.radius**2) / (nbox * nsubbox)

    novrlp=20

    # TODO: Formalise use of only monthlies, see step 3.
    assert land_meta.mavg == 6
    km = 12
    NYRSIN = land_meta.monm/km
    # IYRBGC in the Fortran code
    combined_year_beg = min(land_meta.yrbeg, ocean_meta.yrbeg)
    # index into the combined array of the first year of the land data.
    I1TIN = 12*(land_meta.yrbeg-combined_year_beg)
    # as I1TIN but for ocean data
    I1TINO = 12*(ocean_meta.yrbeg-combined_year_beg)
    # combined_n_months is MONMC in the Fortran.
    combined_n_months = max(land_meta.monm + I1TIN,
                            land_meta.monm + I1TINO)
    # 
    # Indices into the combined arrays for the base period (which is a
    # parameter).
    nfb = base[0] - combined_year_beg
    nlb = base[1] - combined_year_beg

    info = [land_meta.mo1, land_meta.kq, land_meta.mavg, land_meta.monm,
            land_meta.monm4, land_meta.yrbeg, land_meta.missing_flag,
            land_meta.precipitation_flag]

    info[3] = land_meta.monm
    info[4] = 2 * land_meta.monm + 5
    info[5] = combined_year_beg
    boxf.writeline(struct.pack('%s8i' % bos, *info) + land_meta.title)

    # TODO: Use giss_data
    XBAD = land_meta.missing_flag

    # :todo: do we really need the area array to be 8000 cells long?
    for nr,box in enumerate(eqarea.grid()):
        # Averages for the land and ocean (one series per subbox)...
        avg = [[XBAD]*combined_n_months for _ in range(2*nsubbox)]
        area = [km2persubbox] * nsubbox
        wgtc = [0] * (nsubbox*2)
        # Eat the records from land and ocean 100 (nsubbox) at a time.
        # In other words, all 100 subboxes for the box (region).
        landsub = list(itertools.islice(landsubbox, nsubbox))
        oceansub = list(itertools.islice(oceansubbox, nsubbox))
        for i,l,o in zip(range(nsubbox),landsub,oceansub):
            avg[i][I1TIN:I1TIN+len(l.series)] = l.series
            avg[i+nsubbox][I1TINO:I1TINO+len(o.series)] = o.series
            # Count the number of valid entries.
            wgtc[i] = l.good_count
            wgtc[i+nsubbox] = o.good_count
            # :ocean:weight:a: Assign a weight to the ocean cell.
            # A similar calculation appears elsewhere.
            if ignore_land:
                wocn = 0
            else:
                wocn = max(0, (landsub[i].d-rland)/(radius-rland))
            if wgtc[i+nsubbox] < 12*novrlp:
                wocn = 0
            # Normally *intrp* is 0
            if wocn > intrp:
                wocn = 1
            wgtc[i] *= (1 - wocn)
            wgtc[i+nsubbox] *= wocn

        # GISTEMP sort.
        # We want to end up with IORDR, the permutation array that
        # represents the sorter order.  IORDR[0] is the index (into the
        # *wgtc* array) of the longest record, IORDR[1] the index of the
        # next longest record, and so on.  We do that by decorating the
        # *wgtc* array with indexes 0 to 199, and then extracting the
        # (permuted) indexes into IORDR.
        # :todo: should probably import from a purpopse built module.
        from step3 import sort
        z = zip(wgtc, range(2*nsubbox))
        # We only want to compare the weights (because we want to emulate
        # the GISTEMP sort exactly), so we use only the first part of the
        # tuple (that's why we can't just use `cmp`).
        sort(z, lambda x,y: y[0]-x[0])
        wgtc,IORDR = zip(*z)

        # From here to the for loop over the cells (below) we are
        # initialising data for the loop.  Primarily the AVGR and WTR
        # arrays.
        nc = IORDR[0]
        ncr = nc
        if ncr >= nsubbox:
            ncr = nc-nsubbox
        # :ocean:weight:b: Assign weight to ocean cell, see similar
        # calculation, above at :ocean:weight:a.
        # Line 191
        if ignore_land:
            wocn = 0
        else:
            wocn = max(0, (landsub[ncr].d - rland)/(radius-rland))
        if nc == ncr and wgtc[nc + nsubbox] < 12*novrlp:
            wocn = 0
        if wocn > intrp:
            wocn = 1
        wnc = wocn
        if nc < nsubbox:
            wnc = 1 - wocn

        # line 197
        # area is assumed to be constant, so we don't use it here.
        # (which actually avoids a bug that is present in the Fortran, see
        # doc/step5-notes for details).
        wtm = [wnc]*km
        bias = [0]*km
        
        # Weights for the region's record.
        wtr = [0]*combined_n_months
        for m,a in enumerate(avg[nc]):
            if a < XBAD:
                wtr[m] = wnc
        # Create the region (box) record by copying the subbox record
        # into AVGR
        avgr = avg[nc][:]

        # Loop over the remaining cells.
        for n in range(1,2*nsubbox):
            nc = IORDR[n]
            w = wgtc[n]
            # print "nr %(nr)d, n %(n)d, nc %(nc)d, wgtc %(w)d" % locals()
            # Line 207
            # :todo: Can it be correct to use [n]?  It's what the
            # Fortran does.
            if wgtc[n] < 12*novrlp:
                continue
            ncr = nc
            if nc >= nsubbox:
                ncr = nc - nsubbox
            if ignore_land:
                wocn = 0
            else:
                wocn = max(0, (landsub[ncr].d - rland)/(radius-rland))
            if nc == ncr and wgtc[nc + nsubbox] < 12*novrlp:
                wocn = 0
            if wocn > intrp:
                wocn = 1
            wnc = wocn
            if nc < nsubbox:
                wnc = 1 - wocn
            wt1 = wnc
            nsm = combine(avgr, bias, wtr, avg[nc], 0, combined_n_months/km,
              wt1, wtm, km, nc)
        if nfb > 0:
            bias = tavg(avgr, km, NYRSIN, nfb, nlb, True, "Region %d" % nr)
        ngood = 0
        m = 0
        for iy in range(combined_n_months/km):
            for k in range(km):
                m = iy*km + k
                if avgr[m] == XBAD:
                    continue
                avgr[m] -= bias[k]
                ngood += 1

        def nint10x(x):
            return int((10*x) + 0.5)
        def nint(x):
            return int(x+0.5)
        for l in [(map(nint10x, avgr[i:i+12]),map(nint10x, avgr[i+12:i+24]))
                    for i in range(0, combined_n_months, 24)]:
            print >> log, l
        # GISTEMP divdes the weight by TOMETR, but we never multiplied it by
        # the area in the first place.
        for l in [(map(nint, wtr[i:i+12]),map(nint, wtr[i+12:i+24]))
                    for i in range(0, combined_n_months, 24)]:
            print >> log, l
        # MONM or MONMC?
        fmt = '%s%df' % (bos, combined_n_months)
        boxf.writeline(
          struct.pack(fmt, *avgr) +
          struct.pack(fmt, *wtr) +
          struct.pack('%si' % bos, ngood) +
          struct.pack('%s4i' % bos, *box)
          )


# :todo: This was nabbed from code/step3.py.  Put it in one place and
# make it common.
#
# Equivalent of the Fortran subroutine CMBINE
# Parameters as per Fortran except that nsm is returned directly.
def combine(avg, bias, wt, dnew, nf1, nl1, wt1, wtm, km, id,
  NOVRLP=20, XBAD=9999):
    """Run the GISTEMP combining algorithm.  This combines the data
    in the *dnew* array into the *avg* array (also updating the *bias*
    array).

    Each of the arguments *avg*, *wt*, *dnew* is a linear array that is
    divided into "years" by considering each contiguous segment of
    *km* elements a year.  Only data for years in range(nf1, nl1) are
    considered and combined.  Note that range(nf1, nl1) includes *nf1*
    but excludes *nl1* (and that this differs from the Fortran
    convention).
    
    Each month (or other subdivision, such as season, according to
    *km*) of the year is considered separately.  For the set of times
    where both *avg* and *dnew* have data the mean difference (a bias)
    is computed.  If there are fewer than *NOVRLP* years in common the
    data (for that month of the year) are not combined.  The bias is
    subtracted from the *dnew* record and it is point-wise combined
    into *avg* according to the weight *wt1* and the exist
    weight for *avg*.

    *id* is an identifier used only when diagnostics are issued
    (when combining stations it is expected to be the station ID; when
    combining subboxes it is expected to be the subbox number (0 to 99)).
    """

    # In the absence of type checks, check that the arrays have an
    # accessible element.
    avg[0]
    bias[km-1]
    wt[0]
    dnew[0]
    wtm[km-1]
    assert nf1 < nl1
    assert wt1 >= 0

    # This is somewhat experimental.  *wt1* the weight of the incoming
    # data, *dnew*, can either be a scalar (applies to the entire *dnew*
    # series) or a list (in which case each element is the weight of the
    # corresponding element of *dnew*).  (zonav uses the list form).
    # In the body of this function we treat *wt1* as an indexable
    # object.  Here we convert scalars to an object that always returns
    # a constant.
    try:
        wt1[0]
        def update_bias():
            pass
    except TypeError:
        wt1_constant = wt1
        def update_bias():
            """Find mean bias."""
            wtmnew = wtm[k]+wt1_constant
            bias[k] = float(wtm[k]*bias[k]+wt1_constant*biask)/wtmnew
            wtm[k]=wtmnew
            return
        class constant_list:
            def __getitem__(self, i):
                return wt1_constant
        wt1 = constant_list()

    # See to.SBBXgrid.f lines 519 and following

    # The Fortran code handles the arrays by just assuming them to
    # be 2D arrays of shape (*,KM).  Sadly Python array handling
    # just isn't that convenient, so look out for repeated uses of
    # "[k+km*n]" instead.

    nsm = 0
    missed = km
    missing = [True]*km
    for k in range(km):
        sumn = 0    # Sum of data in dnew
        sum = 0     # Sum of data in avg
        ncom = 0    # Number of years where both dnew and avg are valid
        for n in range(nf1, nl1):
            kn = k+km*n     # CSE for array index
            # Could specify that arguments are array.array and use
            # array.count(BAD) and sum, instead of this loop.
            if avg[kn] >= XBAD or dnew[kn] >= XBAD:
                continue
            ncom += 1
            sum += avg[kn]
            sumn += dnew[kn]
        if ncom < NOVRLP:
            continue

        biask = float(sum-sumn)/ncom
        update_bias()

        # Update period of valid data, averages and weights
        for n in range(nf1, nl1):
            kn = k+km*n     # CSE for array index
            if dnew[kn] >= XBAD:
                continue
            wtnew = wt[kn] + wt1[kn]
            avg[kn] = float(wt[kn]*avg[kn] + wt1[kn]*(dnew[kn]+biask))/wtnew
            wt[kn] = wtnew
            nsm += 1
        missed -= 1
        missing[k] = False
    if False and missed > 0:
        print "Unused data - ID/SUBBOX,WT", id, wt1, missing
    return nsm


# :todo: make common with step3.py
# Equivalent to Fortran subroutine TAVG.  Except the bias array
# (typically 12 elements) is returned.
# See to.SBBXgrid.f lines 563 and following.
def tavg(data, km, nyrs, base, limit, nr, id, deflt=0.0, XBAD=9999):
    """:meth:`tavg` computes the time averages (separately for each calendar
    month if *km*=12) over the base period (year *base* to *limit*) and
    saves them in *bias* (a fresh array that is returned).
    
    In case of no data, the average is set to
    *deflt* if nr=0 or computed over the whole period if nr>0.

    Similarly to :meth:`combine` *data* is treated as a linear array divided
    into years by considering contiguous chunks of *km* elements.

    *id* is an arbitrary printable value used for identification in
    diagnostic output (for example, the cell number).

    Note: the Python convention for *base* and *limit* is used, the base
    period consists of the years starting at *base* and running up to,
    but including, the year *limit*.
    """

    bias = [0.0]*km
    missed = km
    len = km*[0]    # Warning: shadows builtin "len"
    for k in range(km):
        bias[k] = deflt
        sum = 0.0
        m = 0
        for n in range(base, limit):
            kn = k+km*n     # CSE for array index
            if data[kn] >= XBAD:
                continue
            m += 1
            sum += data[kn]
        len[k] = m
        if m == 0:
            continue
        bias[k] = float(sum)/float(m)
        missed -= 1
    if nr*missed == 0:
        return bias
    # Base period is data free (for at least one month); use bias
    # with respect to whole series.
    for k in range(km):
        if len[k] > 0:
            continue
        print "No data in base period - MONTH,NR,ID", k, nr, id
        sum = 0.0
        m = 0
        for n in range(nyrs):
            kn = k+km*n     # CSE for array index
            if data[kn] >= XBAD:
                continue
            m += 1
            sum += data[kn]
        if m == 0:
            continue
        bias[k] = float(sum)/float(m)
    return bias


def step5(inputs=()):
    """Step 5 of the GISS processing.

    This step take input provided by steps 3 and 4.

    :Param land, ocean:
        These are data sources for the land and ocean sub-box data.
        They need to support the protocol defined by
        `code.giss_data.SubboxSetProtocol`.

    """
    land, ocean = inputs
    #ocean = open(os.path.join('work', 'SBBX.HadR2'), 'rb')
    box = open(os.path.join('result', 'BX.Ts.ho2.GHCN.CL.PA.1200'), 'wb')
    log = open(os.path.join('log', 'SBBXotoBX.log'), 'w')
    SBBXtoBX(land, ocean, box, log, rland=100, intrp=0)
    # necessary, because box is an input to the next stage, so the file
    # needs to be fully written.
    box.close()

    import zonav
    zonav.main()
    import annzon
    annzon.main()
