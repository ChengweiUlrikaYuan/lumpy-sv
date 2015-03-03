#!/usr/bin/env python -u
from operator import add
import time
import sys
import numpy as np
import glob
from operator import add
from optparse import OptionParser
from sets import Set
import l_bp

def print_var_line(l):
    A = l.rstrip().split('\t')
    if A[4] not in ['<DEL>', '<DUP>', '<INV>']:
        [sv_type,chr_l,chr_r,start_l,end_l,start_r,end_r,m] = l_bp.split_v(l)

        CHROM = chr_r
        POS = m['END']
        ID = A[2] + '_2'
        REF = 'N'
        ALT = ''
        if ']' in A[4]:
            ALT = '[' + chr_l + ':' + A[1] + '[N'
        else:
            ALT = 'N]' + chr_l + ':' + A[1] + ']'
        QUAL = '.'
        FILTER = '.'
        SVTYPE = 'BND'
        STRANDS = m['STRANDS']
        END = A[1]
        SVLEN = '0'
        CIPOS = m['CIEND']
        CIEND = m['CIPOS']
        CIPOS95 = m['CIEND95']
        CIEND95 = m['CIPOS95']
        IMPRECISE = 'IMPRECISE'
        SU = m['SU']
        PE = m['PE']
        SR = m['SR']
        PRPOS = m['PREND']
        PREND = m['PRPOS']
        SNAME = m['SNAME']

        INFO = ';'.join(['SVTYPE='   + str(SVTYPE),
                         'STRANDS='  + str(STRANDS),
                         'END='      + str(END),
                         'SVLEN='    + str(SVLEN),
                         'CIPOS='    + str(CIPOS),
                         'CIEND='    + str(CIEND),
                         'CIPOS95='  + str(CIPOS95),
                         'CIEND95='  + str(CIEND95),
                                       str(IMPRECISE),
                         'SU='       + str(SU),
                         'PE='       + str(PE),
                         'SR='       + str(SR),
                         'PRPOS='    + str(PRPOS),
                         'PREND='    + str(PREND),
                         'SNAME='    + str(SNAME)])

        O = [CHROM,POS,ID,REF,ALT,QUAL,FILTER,INFO]

        A[2] += '_1'
        print '\t'.join(A)
        print '\t'.join([str(o) for o in O])

    else:
        print l

def merge(BP, sample_order, v_id):
    #sys.stderr.write(str(len(BP)) + '\n')

    if len(BP) == 1:
        ##tack on id to SNAME
        A = BP[0].l.rstrip().split('\t')
        A[7]+= ':' + A[2]
        v_id += 1
        A[2] = str(v_id)
        print_var_line('\t'.join(A))
        return v_id

    # this find the max clique 
    #G = {}
    #l_bp.connect(G, BP, 0)

    #for g in G:
    #    sys.stderr.write( str(g) + '\t' + str(len(G[g].edges)) + '\n')

    #C = []
    #_G = G.copy()
    #while len(_G) != 0:
    #    R = Set()
    #    X = Set()
    #    P = Set(_G.keys())
    #    clique = [x for x in l_bp.bron_kerbosch(_G, R, P, X)]
    #    max_clique = sorted(clique, key=len)[0]
    #    sys.stderr.write(str(max_clique) +'\n')
    #    C.append(list(max_clique))
    #    # remove these from the graph
    #    for g in _G:
    #        E = [e for e in _G[g].edges if e[0] not in clique]
    #        G[g].edges = E
    #    for c in max_clique:
    #        del _G[c]

    #Sweep the set.  Find the largest intersecting set.  Remove it.  Continue.
    import heapq

    BP.sort(key=lambda x: x.start_l)

    BP_i = range(len(BP))
    C = []

    #print BP_i

    while len(BP_i) > 0:
        h_l = []
        max_c = []
        max_c_len = 0
        for i in BP_i:
            while (len(h_l) > 0) and (h_l[0][0] < BP[i].start_l):
                heapq.heappop(h_l)

            heapq.heappush(h_l, (BP[i].end_l, i))

            # at this point everything in h_l intersects on the left
            # but we need to take into account what is going on on the right 
            h_r = []
            h_l_i = [x[1] for x in h_l]
            h_l_i.sort(key=lambda x:BP[x].start_r)
            for j in h_l_i:
                while (len(h_r) > 0) and (h_r[0][0] < BP[j].start_r):
                    heapq.heappop(h_r)

                heapq.heappush(h_r, (BP[j].end_r, j))

                if max_c_len < len(h_r):
                    max_c_len = len(h_r)
                    max_c = [y[1] for y in h_r]

        C.append(max_c)
        for c in max_c:
            BP_i.remove(c)

    for c in C:
        L = []
        R = []
        #for g_i in c:
        for b_i in c:
            #b = G[g_i].b
            b = BP[b_i]
            L.append([b.start_l,b.end_l,b.p_l])
            R.append([b.start_r,b.end_r,b.p_r])

        [start_R, end_R, a_R] = l_bp.align_intervals(R)
        [start_L, end_L, a_L] = l_bp.align_intervals(L)

        p_L = [1] * len(a_L[0])
        p_R = [1] * len(a_R[0])

        for c_i in range(len(c)):
            for i in range(len(a_L[c_i])):
                #p_L[i] = p_L[i] * a_L[c_i][i]
                p_L[i] += a_L[c_i][i]

            for i in range(len(a_R[c_i])):
                #p_R[i] = p_R[i] * a_R[c_i][i]
                p_R[i] += a_R[c_i][i]

        sum_L = sum(p_L)
        sum_R = sum(p_R)
        p_L = [x/sum_L for x in p_L]
        p_R = [x/sum_L for x in p_R]

        [clip_start_L, clip_end_L] = l_bp.trim(p_L)
        [clip_start_R, clip_end_R] = l_bp.trim(p_R)

        new_start_L = start_L + clip_start_L
        new_end_L = end_L - clip_end_L

        new_start_R = start_R + clip_start_R
        new_end_R = end_R - clip_end_R

        p_L = p_L[clip_start_L:len(p_L)-clip_end_L]
        p_R = p_R[clip_start_R:len(p_R)-clip_end_R]

        s_p_L = sum(p_L)
        s_p_R = sum(p_R)

        p_L = [x/s_p_L for x in p_L]
        p_R = [x/s_p_R for x in p_R]

        max_i_L = p_L.index(max(p_L))
        max_i_R = p_R.index(max(p_R))

        ninefive_i_L_start = max_i_L
        ninefive_i_L_end = max_i_L
        ninefive_i_L_total = p_L[max_i_L]
        updated = 0
        while (ninefive_i_L_total < 0.95):
                if ninefive_i_L_start > 0:
                    ninefive_i_L_start -= 1
                    ninefive_i_L_total += p_L[ninefive_i_L_start]
                    updated = 1
                if ninefive_i_L_end < len(p_L)-1:
                    ninefive_i_L_end += 1
                    ninefive_i_L_total += p_L[ninefive_i_L_end]
                    updated = 1
                if not updated:
                    break

        ninefive_i_R_start = max_i_R
        ninefive_i_R_end = max_i_R
        ninefive_i_R_total = p_R[max_i_R]
        updated = 0
        while (ninefive_i_R_total < 0.95):
                if ninefive_i_R_start > 0:
                    ninefive_i_R_start -= 1
                    ninefive_i_R_total += p_R[ninefive_i_R_start]
                    updated = 1
                if ninefive_i_R_end < len(p_R)-1:
                    ninefive_i_R_end += 1
                    ninefive_i_R_total += p_R[ninefive_i_R_end]
                    updated = 1
                if not updated:
                    break
 
        CIPOS95=str(ninefive_i_L_start) + ',' + str(ninefive_i_L_end)
        CIEND95=str(ninefive_i_R_start) + ',' + str(ninefive_i_R_end)

        #CHROM = G[c[0]].b.chr_l
        CHROM = BP[c[0]].chr_l
        POS = new_start_L + max_i_L
        v_id += 1
        ID = str(v_id)
        REF = 'N'

        ALT = ''
        #if G[c[0]].b.sv_type == 'BND':
        if BP[c[0]].sv_type == 'BND':
            #G[c[0]].b.chr_r + \
            ALT = 'N]' + \
                   BP[c[0]].chr_r + \
                   ':' + \
                   str(new_start_R + max_i_R) + \
                   ']'
        else:
            #ALT = '<' + G[c[0]].b.sv_type + '>'
            ALT = '<' + BP[c[0]].sv_type + '>'
        QUAL = '.'
        FILTER = '.'
        #FORMAT = G[c[0]].b.l.split('\t')[8]
        FORMAT = BP[c[0]].l.split('\t')[8]
        #SVTYPE = G[c[0]].b.sv_type
        SVTYPE = BP[c[0]].sv_type

        STRANDS = ''
        strand_map = {}
        e_type_map = {}

        SU = 0
        PE = 0
        SR = 0

        s_name_list = []

        gt_list = [] 

        #for g_i in c:
        for b_i in c:
            #A = G[g_i].b.l.rstrip().split('\t')
            A = BP[b_i].l.rstrip().split('\t')
            m = l_bp.to_map(A[7])

            for strand_entry in m['STRANDS'].split(','):
                s_type,s_count = strand_entry.split(':')
                if s_type not in strand_map:
                    strand_map[s_type] = 0
                strand_map[s_type] += int(s_count)

            SU += int(m['SU'])
            PE += int(m['PE'])
            SR += int(m['SR'])

            s_name_list.append(m['SNAME'] + ':' + A[2])

            gt_list += A[9:]

        SNAME=','.join(s_name_list)

        GTS = '\t'.join(gt_list)

        strand_types_counts = []
        for strand in strand_map:
            strand_types_counts.append(strand + ':' + str(strand_map[strand]))
        STRANDS = ','.join(strand_types_counts)

        SVLEN = (new_start_L + max_i_L) - (new_start_R + max_i_R)
        END = new_start_R + max_i_R
        CIPOS=','.join([str(x) for x in [-1*max_i_L, len(p_L) - max_i_L - 1]])
        CIEND=','.join([str(x) for x in [-1*max_i_R, len(p_R) - max_i_R - 1]])
        IMPRECISE='IMPRECISE'
        PRPOS=','.join([str(x) for x in p_L])
        PREND=','.join([str(x) for x in p_R])

        INFO = ';'.join(['SVTYPE='   + str(SVTYPE),
                         'STRANDS='  + str(STRANDS),
                         'END='      + str(END),
                         'SVLEN='    + str(SVLEN),
                         'CIPOS='    + str(CIPOS),
                         'CIEND='    + str(CIEND),
                         'CIPOS95='  + str(CIPOS95),
                         'CIEND95='  + str(CIEND95),
                                       str(IMPRECISE),
                         'SU='       + str(SU),
                         'PE='       + str(PE),
                         'SR='       + str(SR),
                         'PRPOS='    + str(PRPOS),
                         'PREND='    + str(PREND),
                         'SNAME='    + str(SNAME)])

        #O = [CHROM,POS,ID,REF,ALT,QUAL,FILTER,INFO,FORMAT,GTS]
        O = [CHROM,POS,ID,REF,ALT,QUAL,FILTER,INFO]

        print_var_line('\t'.join([str(o) for o in O]))
    return v_id

def r_cluster(BP_l, sample_order, v_id):
    # need to resort based on the right side, then extract clusters
    BP_l.sort(key=lambda x: x.start_r)
    BP_l.sort(key=lambda x: x.chr_r)

    BP_r = []
    BP_max_end_r = -1
    BP_chr_r = ''

    for b in BP_l:
        if (len(BP_r) == 0) or \
           ((b.start_r <= BP_max_end_r) and \
           (b.chr_r == BP_chr_r)):
            BP_r.append(b)
            BP_max_end_r = max(BP_max_end_r, b.end_r)
            BP_chr_r = b.chr_r
        else:
            #print len(BP_r)
            v_id = merge(BP_r, sample_order, v_id)
            BP_r = [b]
            BP_max_end_r = b.end_r
            BP_chr_r = b.chr_r
 
    if len(BP_r) > 0:
        #print len(BP_r)
        v_id = merge(BP_r, sample_order, v_id)

    return v_id

def l_cluster(file_name):
    v_id = 0
    vcf_lines = []
    vcf_headers = Set()
    r = l_bp.parse_vcf(file_name, vcf_lines, vcf_headers, add_sname=False)

    vcf_headers.add("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")


    sample_order = []
    for header in vcf_headers:
        if header[:8] == '##SAMPLE':
            sample_order.append(header.rstrip()[13:-1])
        #elif header[:8] == '##FORMAT':
            #i,n,t=header[header.find('<')+1:header.find('>')].split(',')[0:3]
            #print i,n,t

    #exit(1)

    vcf_headers = list(vcf_headers)
    vcf_headers.sort(cmp=l_bp.header_line_cmp)
    for h in vcf_headers:
        print h,

    BP_l = []
    BP_sv_type = ''
    BP_max_end_l = -1
    BP_chr_l = ''

    for l in vcf_lines:
        b = l_bp.breakpoint(l)

        if (len(BP_l) == 0) or \
           ((b.start_l <= BP_max_end_l) and \
            (b.chr_l == BP_chr_l) and \
            (b.sv_type == BP_sv_type)):
            BP_l.append(b)
            BP_max_end_l = max(BP_max_end_l, b.end_l)
            BP_chr_l = b.chr_l
            BP_sv_type = b.sv_type
        else:
            #print len(BP_l)
            v_id = r_cluster(BP_l, sample_order, v_id)
            BP_l = [b]
            BP_max_end_l = b.end_l
            BP_sv_type = b.sv_type
            BP_chr_l = b.chr_l

    if len(BP_l) > 0:
        #print len(BP_l)
        v_id = r_cluster(BP_l, sample_order, v_id)
 

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main():

    usage = """%prog -i <file>
lmerge
Author: Ryan Layer & Ira Hall
Description: merge lumpy calls.
Version: ira_7
    """

    parser = OptionParser(usage)
    parser.add_option("-i", \
                      "--inFile", \
                      dest="inFile",
                      help="A sorted lumpy output file generated by " + \
                           "lsort; or stdin (-i stdin). Column 7 must " + \
                           "have the format sample:variantID", \
                           metavar="FILE")

    (opts, args) = parser.parse_args()

    #if opts.inFile is None or opts.configFile is None:
    if opts.inFile is None:
        parser.print_help()
        print
    else:
        try:
            l_cluster(opts.inFile)
        except IOError as err:
            sys.stderr.write("IOError " + str(err) + "\n");
            return

if __name__ == "__main__":
    sys.exit(main())
