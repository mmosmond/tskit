#
# Copyright (C) 2016 University of Oxford
#
# This file is part of msprime.
#
# msprime is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# msprime is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with msprime.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Test cases for generalized statistic computation.
"""
from __future__ import print_function
from __future__ import division


import unittest
import random

import numpy as np
import numpy.testing as nt

import six

import msprime


def path_length(tr, x, y):
    L = 0
    mrca = tr.mrca(x, y)
    for u in x, y:
        while u != mrca:
            L += tr.branch_length(u)
            u = tr.parent(u)
    return L


class PythonTreeStatCalculator(object):
    """
    Python implementations of various ("tree") branch-length statistics -
    inefficient but more clear what they are doing.  
    """

    def __init__(self, tree_sequence):
        self.tree_sequence = tree_sequence

    def tree_length_diversity(self, X, Y, begin=0.0, end=None):
        '''
        Computes average pairwise diversity between a random choice from x
        and a random choice from y over the window specified.
        '''
        if end is None:
            end = self.tree_sequence.sequence_length
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            SS = 0
            for x in X:
                for y in Y:
                    SS += path_length(tr, x, y)
            S += SS*(min(end, tr.interval[1]) - max(begin, tr.interval[0]))
        return S/((end-begin)*len(X)*len(Y))

    def tree_length_diversity_window(self, X, Y, windows):
        out = [self.tree_length_diversity(X, Y, windows[k], windows[k+1])
               for k in range(len(windows)-1)]
        return out

    def tree_length_Y3(self, X, Y, Z, begin=0.0, end=None):
        if end is None:
            end = self.tree_sequence.sequence_length
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            this_length = min(end, tr.interval[1]) - max(begin, tr.interval[0])
            for x in X:
                for y in Y:
                    for z in Z:
                        xy_mrca = tr.mrca(x, y)
                        xz_mrca = tr.mrca(x, z)
                        yz_mrca = tr.mrca(y, z)
                        if xy_mrca == xz_mrca:
                            #   /\
                            #  / /\
                            # x y  z
                            S += path_length(tr, x, yz_mrca) * this_length
                        elif xy_mrca == yz_mrca:
                            #   /\
                            #  / /\
                            # y x  z
                            S += path_length(tr, x, xz_mrca) * this_length
                        elif xz_mrca == yz_mrca:
                            #   /\
                            #  / /\
                            # z x  y
                            S += path_length(tr, x, xy_mrca) * this_length
        return S/((end - begin) * len(X) * len(Y) * len(Z))

    def tree_length_Y2(self, X, Y, begin=0.0, end=None):
        if end is None:
            end = self.tree_sequence.sequence_length
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            this_length = min(end, tr.interval[1]) - max(begin, tr.interval[0])
            for x in X:
                for y in Y:
                    for z in set(Y) - set([y]):
                        xy_mrca = tr.mrca(x, y)
                        xz_mrca = tr.mrca(x, z)
                        yz_mrca = tr.mrca(y, z)
                        if xy_mrca == xz_mrca:
                            #   /\
                            #  / /\
                            # x y  z
                            S += path_length(tr, x, yz_mrca) * this_length
                        elif xy_mrca == yz_mrca:
                            #   /\
                            #  / /\
                            # y x  z
                            S += path_length(tr, x, xz_mrca) * this_length
                        elif xz_mrca == yz_mrca:
                            #   /\
                            #  / /\
                            # z x  y
                            S += path_length(tr, x, xy_mrca) * this_length
        return S/((end - begin) * len(X) * len(Y) * (len(Y)-1))

    def tree_length_Y1(self, X, begin=0.0, end=None):
        if end is None:
            end = self.tree_sequence.sequence_length
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            this_length = min(end, tr.interval[1]) - max(begin, tr.interval[0])
            for x in X:
                for y in set(X) - set([x]):
                    for z in set(X) - set([x, y]):
                        xy_mrca = tr.mrca(x, y)
                        xz_mrca = tr.mrca(x, z)
                        yz_mrca = tr.mrca(y, z)
                        if xy_mrca == xz_mrca:
                            #   /\
                            #  / /\
                            # x y  z
                            S += path_length(tr, x, yz_mrca) * this_length
                        elif xy_mrca == yz_mrca:
                            #   /\
                            #  / /\
                            # y x  z
                            S += path_length(tr, x, xz_mrca) * this_length
                        elif xz_mrca == yz_mrca:
                            #   /\
                            #  / /\
                            # z x  y
                            S += path_length(tr, x, xy_mrca) * this_length
        return S/((end - begin) * len(X) * (len(X)-1) * (len(X)-2))

    def tree_length_f4(self, A, B, C, D, begin=0.0, end=None):
        if end is None:
            end = self.tree_sequence.sequence_length
        for U in A, B, C, D:
            if max([U.count(x) for x in set(U)]) > 1:
                raise ValueError("A,B,C, and D cannot contain repeated elements.")
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            this_length = min(end, tr.interval[1]) - max(begin, tr.interval[0])
            SS = 0
            for a in A:
                for b in B:
                    for c in C:
                        for d in D:
                            SS += path_length(tr, tr.mrca(a, c), tr.mrca(b, d))
                            SS -= path_length(tr, tr.mrca(a, d), tr.mrca(b, c))
            S += SS * this_length
        return S / ((end - begin) * len(A) * len(B) * len(C) * len(D))

    def tree_length_f3(self, A, B, C, begin=0.0, end=None):
        # this is f4(A,B;A,C) but drawing distinct samples from A
        if end is None:
            end = self.tree_sequence.sequence_length
        assert(len(A) > 1)
        for U in A, B, C:
            if max([U.count(x) for x in set(U)]) > 1:
                raise ValueError("A, B and C cannot contain repeated elements.")
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            this_length = min(end, tr.interval[1]) - max(begin, tr.interval[0])
            SS = 0
            for a in A:
                for b in B:
                    for c in set(A) - set([a]):
                        for d in C:
                            SS += path_length(tr, tr.mrca(a, c), tr.mrca(b, d))
                            SS -= path_length(tr, tr.mrca(a, d), tr.mrca(b, c))
            S += SS * this_length
        return S / ((end - begin) * len(A) * (len(A) - 1) * len(B) * len(C))

    def tree_length_f2(self, A, B, begin=0.0, end=None):
        # this is f4(A,B;A,B) but drawing distinct samples from A and B
        if end is None:
            end = self.tree_sequence.sequence_length
        assert(len(A) > 1)
        for U in A, B:
            if max([U.count(x) for x in set(U)]) > 1:
                raise ValueError("A and B cannot contain repeated elements.")
        S = 0
        for tr in self.tree_sequence.trees():
            if tr.interval[1] <= begin:
                continue
            if tr.interval[0] >= end:
                break
            this_length = min(end, tr.interval[1]) - max(begin, tr.interval[0])
            SS = 0
            for a in A:
                for b in B:
                    for c in set(A) - set([a]):
                        for d in set(B) - set([b]):
                            SS += path_length(tr, tr.mrca(a, c), tr.mrca(b, d))
                            SS -= path_length(tr, tr.mrca(a, d), tr.mrca(b, c))
            S += SS * this_length
        return S / ((end - begin) * len(A) * (len(A) - 1) * len(B) * (len(B) - 1))

    def tree_stat(self, sample_sets, weight_fun, begin=0.0, end=None):
        '''
        Here sample_sets is a list of lists of samples, and weight_fun is a function
        whose argument is a list of integers of the same length as sample_sets
        that returns a number.  Each branch in a tree is weighted by weight_fun(x),
        where x[i] is the number of samples in sample_sets[i] below that
        branch.  This finds the sum of all counted branches for each tree,
        and averages this across the tree sequence ts, weighted by genomic length.

        This version is inefficient as it iterates over all nodes in each tree.
        '''
        out = self.tree_stat_vector(sample_sets, 
                                    lambda x: [weight_fun(x)],
                                    begin=begin, end=end)
        if len(out) > 1:
            raise ValueError("Expecting output of length 1.")
        return out[0]

    def tree_stat_vector(self, sample_sets, weight_fun, begin=0.0, end=None):
        '''
        Here sample_sets is a list of lists of samples, and weight_fun is a function
        whose argument is a list of integers of the same length as sample_sets
        that returns a list of numbers; there will be one output for each element.
        For each value, each branch in a tree is weighted by weight_fun(x),
        where x[i] is the number of samples in sample_sets[i] below that
        branch.  This finds the sum of all counted branches for each tree,
        and averages this across the tree sequence ts, weighted by genomic length.

        This version is inefficient as it iterates over all nodes in each tree.
        '''
        for U in sample_sets:
            if max([U.count(x) for x in set(U)]) > 1:
                raise ValueError("elements of sample_sets cannot contain repeated elements.")
        if end is None:
            end = self.tree_sequence.sequence_length
        tr_its = [self.tree_sequence.trees(
                        tracked_samples=x,
                        sample_counts=True,
                        sample_lists=True) for x in sample_sets]
        n_out = len(weight_fun([0 for a in sample_sets]))
        S = [0.0 for j in range(n_out)]
        for k in range(self.tree_sequence.num_trees):
            trs = [next(x) for x in tr_its]
            root = trs[0].root
            tr_len = min(end, trs[0].interval[1]) - max(begin, trs[0].interval[0])
            if tr_len > 0:
                for node in trs[0].nodes():
                    if node != root:
                        x = [tr.num_tracked_samples(node) for tr in trs]
                        w = weight_fun(x)
                        for j in range(n_out):
                            S[j] += w[j] * trs[0].branch_length(node) * tr_len
        for j in range(n_out):
            # the notorious factor of 2
            S[j] *= (2.0/(end-begin))
        return S


class PythonSiteStatCalculator(object):
    """
    Python implementations of various single-site statistics -
    inefficient but more clear what they are doing.  
    """

    def __init__(self, tree_sequence):
        self.tree_sequence = tree_sequence

    def tree_stat_vector(self, sample_sets, weight_fun, begin=0.0, end=None):
        '''
        Here sample_sets is a list of lists of samples, and weight_fun is a function
        whose argument is a list of integers of the same length as sample_sets
        that returns a list of numbers; there will be one output for each element.
        For each value, each allele in a tree is weighted by weight_fun(x), where
        x[i] is the number of samples in sample_sets[i] that inherit that allele.
        This finds the sum of this value for all alleles at all polymorphic sites,
        and across the tree sequence ts, weighted by genomic length.

        This version is inefficient as it works directly with haplotypes.
        '''
        for U in sample_sets:
            if max([U.count(x) for x in set(U)]) > 1:
                raise ValueError("elements of sample_sets cannot contain repeated elements.")
        if end is None:
            end = self.tree_sequence.sequence_length
        haps = list(self.tree_sequence.haplotypes())
        n_out = len(weight_fun([0 for a in sample_sets]))
        S = [0.0 for j in range(n_out)]
        site_positions = [x.position for x in self.tree_sequence.sites()]
        for k in range(self.tree_sequence.num_sites):
            if (site_positions[k] >= begin) and (site_positions[k] < end):
                all_g = [haps[j][k] for j in range(self.tree_sequence.num_samples)]
                g = [[haps[j][k] for j in u] for u in sample_sets]
                for a in set(all_g):
                    x = [h.count(a) for h in g]
                    w = weight_fun(x)
                    for j in range(n_out):
                        S[j] += w[j]
        for j in range(n_out):
            S[j] /= (end - begin)
        return S

    def tree_stat(self, sample_sets, weight_fun, begin=0.0, end=None):
        '''
        This provides a non-vectorized interface to `tree_stat_vector()`.
        '''
        out = self.tree_stat_vector(sample_sets, lambda x: [weight_fun(x)],
                                    begin=begin, end=end)
        if len(out) > 1:
            raise ValueError("Expecting output of length 1.")
        return out[0]


def upper_tri_to_matrix(x):
    """
    Given x, a vector of entries of the upper triangle of a matrix
    in row-major order, including the diagonal, return the corresponding matrix.
    """
    # n^2 + n = 2 u => n = (-1 + sqrt(1 + 8*u))/2
    n = int((np.sqrt(1 + 8 * len(x)) - 1)/2.0)
    out = np.ones((n, n))
    k = 0
    for i in range(n):
        for j in range(i, n):
            out[i, j] = out[j, i] = x[k]
            k += 1
    return out


class GeneralStatsTestCase(unittest.TestCase):
    """
    Tests of statistic computation.
    """
    random_seed = 123456

    def assertListAlmostEqual(self, x, y):
        self.assertEqual(len(x), len(y))
        for a, b in zip(x, y):
            self.assertAlmostEqual(a, b)

    def assertArrayEqual(self, x, y):
        nt.assert_equal(x, y)

    def assertArrayAlmostEqual(self, x, y):
        nt.assert_array_almost_equal(x, y)

    def compare_stats(self, ts, tree_fn, leaf_sets, index_length,
                      tsc_fn=None, tsc_vector_fn=None):
        """
        Use to compare a tree sequence method tsc_vector_fn to a single-window-based
        implementation tree_fn that takes index_length leaf sets at once.  Pass
        index_length=0 to signal that tsc_fn does not take an 'indices' argument;
        otherwise, gives the length of each of the tuples.

        Here are the arguments these functions will get:
            tree_fn(leaf_set[i], ... , leaf_set[k], begin=left, end=right)
            tsc_vector_fn(leaf_sets, windows, indices)
            ... or tsc_vector_fn(leaf_sets, windows)
            tsc_fn(leaf_sets, windows)
        """
        assert(len(leaf_sets) > index_length)
        nl = len(leaf_sets)
        windows = [k * ts.sequence_length / 20 for k in
                   [0] + sorted(random.sample(range(1, 20), 4)) + [20]]
        indices = [random.sample(range(nl), max(1, index_length)) for _ in range(5)]
        leafset_args = [[leaf_sets[i] for i in ii] for ii in indices]
        tree_args = [x for x in leafset_args]
        win_args = [{'begin': windows[i], 'end': windows[i+1]}
                    for i in range(len(windows)-1)]
        tree_vals = [[tree_fn(*a, **b) for a in tree_args] for b in win_args]

        if tsc_vector_fn is not None:
            if index_length > 0:
                tsc_vector_vals = tsc_vector_fn(leaf_sets, windows, indices)
            else:
                tsc_vector_vals = tsc_vector_fn([leaf_sets[i[0]] for i in indices],
                                                windows)
            self.assertEqual(len(tsc_vector_vals), len(windows)-1)
            print("vector:")
            print(tsc_vector_vals)
            print(tree_vals)
            for x in tsc_vector_vals:
                self.assertEqual(len(x), len(indices))
            for i in range(len(windows)-1):
                self.assertListAlmostEqual(tsc_vector_vals[i], tree_vals[i])

        if tsc_fn is not None:
            tsc_vals_orig = [tsc_fn(*([ls] + [windows])) for ls in leafset_args]
            tsc_vals = [[x[k][0] for x in tsc_vals_orig] for k in range(len(windows)-1)]
            self.assertEqual(len(tsc_vals), len(windows)-1)
            print("not:")
            print(tsc_vals)
            print(tree_vals)
            for x in tsc_vals:
                self.assertAlmostEqual(len(x), len(indices))
            for i in range(len(windows)-1):
                self.assertListAlmostEqual(tsc_vals[i], tree_vals[i])

    def check_tree_stat_vector(self, ts, calc1, calc2):
        # test the general tree_stat_vector() machinery
        samples = random.sample(ts.samples(), 12)
        A = [[samples[0], samples[1], samples[6]],
             [samples[2], samples[3], samples[7]],
             [samples[4], samples[5], samples[8]],
             [samples[9], samples[10], samples[11]]]
        tsc = calc1(ts)
        py_tsc = calc2(ts)

        # a made-up example
        def tsf(sample_sets, windows, indices):
            def f(x):
                return [x[i] + 2.0 * x[j] + 3.5 * x[k] for i, j, k in indices]
            return tsc.tree_stat_vector(sample_sets, weight_fun=f, windows=windows)

        def py_tsf(X, Y, Z, begin, end):
            def f(x):
                return x[0] + 2.0 * x[1] + 3.5 * x[2]
            return py_tsc.tree_stat([X, Y, Z], weight_fun=f, 
                                    begin=begin, end=end)

        self.compare_stats(ts, py_tsf, A, 3, tsc_vector_fn=tsf)

    def check_f_stats(self, ts):
        samples = random.sample(ts.samples(), 12)
        A = [[samples[0], samples[1], samples[2]],
             [samples[3], samples[4]],
             [samples[5], samples[6]],
             [samples[7], samples[8]],
             [samples[9], samples[10], samples[11]]]
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)
        self.compare_stats(ts, py_tsc.tree_length_f2, A, 2,
                           tsc_fn=tsc.f2, tsc_vector_fn=tsc.f2_vector)
        self.compare_stats(ts, py_tsc.tree_length_f3, A, 3,
                           tsc_fn=tsc.f3, tsc_vector_fn=tsc.f3_vector)
        self.compare_stats(ts, py_tsc.tree_length_f4, A, 4,
                           tsc_fn=tsc.f4, tsc_vector_fn=tsc.f4_vector)

    def check_Y_stat(self, ts):
        samples = random.sample(ts.samples(), 12)
        A = [[samples[0], samples[1], samples[6]],
             [samples[2], samples[3], samples[7]],
             [samples[4], samples[5], samples[8]],
             [samples[9], samples[10], samples[11]]]
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)
        self.compare_stats(ts, py_tsc.tree_length_Y3, A, 3,
                           tsc_fn=tsc.Y3, tsc_vector_fn=tsc.Y3_vector)
        self.compare_stats(ts, py_tsc.tree_length_Y2, A, 2,
                           tsc_fn=tsc.Y2, tsc_vector_fn=tsc.Y2_vector)
        self.compare_stats(ts, py_tsc.tree_length_Y1, A, 0,
                           tsc_vector_fn=tsc.Y1_vector)


class TreeStatsTestCase(GeneralStatsTestCase):
    """
    Tests of tree statistic computation.
    """

    def check_tree_stat_vector(self, ts):
        super().check_tree_stat_vector(ts, calc1=msprime.TreeStatCalculator,
                                       calc2=PythonTreeStatCalculator)

    def check_pairwise_diversity(self, ts):
        samples = random.sample(ts.samples(), 2)
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)
        A_one = [[samples[0]], [samples[1]]]
        A_many = [random.sample(ts.samples(), 2),
                  random.sample(ts.samples(), 2)]
        for A in (A_one, A_many):
            n = [len(a) for a in A]

            def f(x):
                return float(x[0]*(n[1]-x[1]) + (n[0]-x[0])*x[1])/float(2*n[0]*n[1])

            self.assertAlmostEqual(
                    py_tsc.tree_stat(A, f),
                    py_tsc.tree_length_diversity(A[0], A[1]))
            self.assertAlmostEqual(
                    tsc.tree_stat(A, f),
                    py_tsc.tree_length_diversity(A[0], A[1]))

    def check_tmrca_matrix(self, ts):
        # nonoverlapping samples
        samples = random.sample(ts.samples(), 6)
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)
        A = [samples[0:3], samples[3:5], samples[5:6]]
        windows = [0.0, ts.sequence_length/2, ts.sequence_length]
        ts_values = tsc.mean_pairwise_tmrca(A, windows)
        ts_matrix_values = tsc.mean_pairwise_tmrca_matrix(A, windows)
        self.assertListEqual([len(x) for x in ts_values], [len(samples), len(samples)])
        assert(len(A[2]) == 1)
        self.assertListEqual([x[5] for x in ts_values], [np.nan, np.nan])
        self.assertEqual(len(ts_values), len(ts_matrix_values))
        for w in range(len(ts_values)):
            self.assertArrayEqual(
                    ts_matrix_values[w, :, :],
                    upper_tri_to_matrix(ts_values[w]))
        here_values = np.array([[[py_tsc.tree_length_diversity(A[i], A[j],
                                                               begin=windows[k],
                                                               end=windows[k+1])
                                  for i in range(len(A))]
                                 for j in range(len(A))]
                                for k in range(len(windows)-1)])
        for k in range(len(windows)-1):
            for i in range(len(A)):
                for j in range(len(A)):
                    if i == j:
                        if len(A[i]) == 1:
                            here_values[k, i, i] = np.nan
                        else:
                            here_values[k, i, i] /= 2.0 * (len(A[i])-1)/len(A[i])
                    else:
                        here_values[k, j, i] /= 2.0
        for k in range(len(windows)-1):
            self.assertArrayAlmostEqual(here_values[k], ts_matrix_values[k])

    def test_errors(self):
        ts = msprime.simulate(10, random_seed=self.random_seed, recombination_rate=10)
        tsc = msprime.TreeStatCalculator(ts)
        self.assertRaises(ValueError,
                          tsc.mean_pairwise_tmrca, [[0], [11]], [0, ts.sequence_length])
        self.assertRaises(ValueError,
                          tsc.mean_pairwise_tmrca, [[0], [1]], [0, ts.sequence_length/2])
        self.assertRaises(ValueError,
                          tsc.mean_pairwise_tmrca, [[0], [1]], [ts.sequence_length/2,
                                                                ts.sequence_length])
        self.assertRaises(ValueError,
                          tsc.mean_pairwise_tmrca, [[0], [1]], [0.0, 2.0, 1.0,
                                                                ts.sequence_length])
        # errors for not enough sample_sets
        self.assertRaises(ValueError,
                          tsc.f4, [[0, 1], [2], [3]], [0, ts.sequence_length])
        self.assertRaises(ValueError,
                          tsc.f3, [[0], [2]], [0, ts.sequence_length])
        self.assertRaises(ValueError,
                          tsc.f2, [[0], [1], [2]], [0, ts.sequence_length])
        # errors if indices aren't of the right length
        self.assertRaises(ValueError,
                          tsc.Y3_vector, [[0], [1], [2]], [0, ts.sequence_length],
                          [[0, 1]])
        self.assertRaises(ValueError,
                          tsc.f4_vector, [[0], [1], [2], [3]], [0, ts.sequence_length],
                          [[0, 1]])
        self.assertRaises(ValueError,
                          tsc.f3_vector, [[0], [1], [2], [3]], [0, ts.sequence_length],
                          [[0, 1]])
        self.assertRaises(ValueError,
                          tsc.f2_vector, [[0], [1], [2], [3]], [0, ts.sequence_length],
                          [[0, 1, 2]])

    def test_windowization(self):
        ts = msprime.simulate(10, random_seed=self.random_seed, recombination_rate=100)
        samples = random.sample(ts.samples(), 2)
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)
        A_one = [[samples[0]], [samples[1]]]
        A_many = [random.sample(ts.samples(), 2),
                  random.sample(ts.samples(), 2)]
        some_breaks = list(set([0.0, ts.sequence_length/2, ts.sequence_length] +
                               random.sample(list(ts.breakpoints()), 5)))
        some_breaks.sort()
        tiny_breaks = ([(k / 4) * list(ts.breakpoints())[1] for k in range(4)] +
                       [ts.sequence_length])
        wins = [[0.0, ts.sequence_length],
                [0.0, ts.sequence_length/2, ts.sequence_length],
                tiny_breaks,
                some_breaks]

        with self.assertRaises(ValueError):
            tsc.tree_stat_vector(A_one, lambda x: 1.0,
                                 windows=[0.0, 1.0, ts.sequence_length+1.1])

        for A in (A_one, A_many):
            for windows in wins:
                n = [len(a) for a in A]

                def f(x):
                    return float(x[0]*(n[1]-x[1]) + (n[0]-x[0])*x[1])/float(2*n[0]*n[1])

                def g(x):
                    return [f(x)]

                tsdiv_v = tsc.tree_stat_vector(A, g, windows)
                tsdiv_vx = [x[0] for x in tsdiv_v]
                tsdiv = tsc.tree_stat_windowed(A, f, windows)
                pydiv = py_tsc.tree_length_diversity_window(A[0], A[1], windows)
                self.assertEqual(len(tsdiv), len(windows)-1)
                self.assertListAlmostEqual(tsdiv, pydiv)
                self.assertListEqual(tsdiv, tsdiv_vx)

    def test_derived_functions(self):
        # Test implementation of statistics using these functions.
        ts = msprime.simulate(20, random_seed=self.random_seed, recombination_rate=100)
        self.check_tree_stat_vector(ts)
        self.check_pairwise_diversity(ts)
        self.check_tmrca_matrix(ts)
        self.check_f_stats(ts)
        self.check_Y_stat(ts)

    def test_case_1(self):
        # With mutations:
        #
        # 1.0          6
        # 0.7         / \                                    5
        #            /   X                                  / \
        # 0.5       X     4                4               /   4
        #          /     / \              / \             /   X X
        # 0.4     X     X   \            X   3           X   /   \
        #        /     /     X          /   / X         /   /     \
        # 0.0   0     1       2        1   0   2       0   1       2
        #          (0.0, 0.2),        (0.2, 0.8),       (0.8, 1.0)
        #
        true_diversity_01 = 2*(1 * (0.2-0) + 0.5 * (0.8-0.2) + 0.7 * (1.0-0.8))
        true_diversity_02 = 2*(1 * (0.2-0) + 0.4 * (0.8-0.2) + 0.7 * (1.0-0.8))
        true_diversity_12 = 2*(0.5 * (0.2-0) + 0.5 * (0.8-0.2) + 0.5 * (1.0-0.8))
        nodes = six.StringIO("""\
        id      is_sample   time
        0       1           0
        1       1           0
        2       1           0
        3       0           0.4
        4       0           0.5
        5       0           0.7
        6       0           1.0
        """)
        edges = six.StringIO("""\
        left    right   parent  child
        0.2     0.8     3       0,2
        0.0     0.2     4       1,2
        0.2     0.8     4       1,3
        0.8     1.0     4       1,2
        0.8     1.0     5       0,4
        0.0     0.2     6       0,4
        """)
        sites = six.StringIO("""\
        id  position    ancestral_state
        0   0.05        0
        1   0.1         0
        2   0.11        0
        3   0.15        0
        4   0.151       0
        5   0.3         0
        6   0.6         0
        7   0.9         0
        8   0.95        0
        9   0.951       0
        """)
        mutations = six.StringIO("""\
        site    node    derived_state
        0       4       1
        1       0       1
        2       2       1
        3       0       1
        4       1       1
        5       1       1
        6       2       1
        7       0       1
        8       1       1
        9       2       1
        """)
        ts = msprime.load_text(
            nodes=nodes, edges=edges, sites=sites, mutations=mutations)
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)
        self.check_pairwise_diversity(ts)
        # TODO check this:
        # self.check_pairwise_diversity_mutations(ts)

        # diversity between 0 and 1
        A = [[0], [1]]

        def f(x):
            return float((x[0] > 0) != (x[1] > 0))/2.0

        # tree lengths:
        self.assertAlmostEqual(py_tsc.tree_length_diversity([0], [1]),
                               true_diversity_01)
        self.assertAlmostEqual(tsc.tree_stat(A, f),
                               true_diversity_01)
        self.assertAlmostEqual(py_tsc.tree_stat(A, f),
                               true_diversity_01)

        # mean diversity between [0, 1] and [0, 2]:
        true_mean_diversity = (0 + true_diversity_02
                               + true_diversity_01 + true_diversity_12)/4
        A = [[0, 1], [0, 2]]
        n = [len(a) for a in A]

        def f(x):
            return float(x[0]*(n[1]-x[1]) + (n[0]-x[0])*x[1])/8.0

        # tree lengths:
        self.assertAlmostEqual(py_tsc.tree_length_diversity(A[0], A[1]),
                               true_mean_diversity)
        self.assertAlmostEqual(tsc.tree_stat(A, f),
                               true_mean_diversity)
        self.assertAlmostEqual(py_tsc.tree_stat(A, f),
                               true_mean_diversity)

        # Y-statistic for (0/12)
        A = [[0], [1, 2]]

        def f(x):
            return float(((x[0] == 1) and (x[1] == 0)) 
                         or ((x[0] == 0) and (x[1] == 2)))/2.0

        # tree lengths:
        true_Y = 0.2*(1 + 0.5) + 0.6*(0.4) + 0.2*(0.7+0.2)
        self.assertAlmostEqual(py_tsc.tree_length_Y3([0], [1], [2]), true_Y)
        self.assertAlmostEqual(tsc.tree_stat(A, f), true_Y)
        self.assertAlmostEqual(py_tsc.tree_stat(A, f), true_Y)

    def test_case_2(self):
        # Here are the trees:
        # t                  |              |              |             |
        #
        # 0       --3--      |     --3--    |     --3--    |    --3--    |    --3--
        #        /  |  \     |    /  |  \   |    /     \   |   /     \   |   /     \
        # 1     4   |   5    |   4   |   5  |   4       5  |  4       5  |  4       5
        #       |\ / \ /|    |   |\   \     |   |\     /   |  |\     /   |  |\     /|
        # 2     | 6   7 |    |   | 6   7    |   | 6   7    |  | 6   7    |  | 6   7 |
        #       | |\ /| |    |   |  \  |    |   |  \  |    |  |  \       |  |  \    | ...
        # 3     | | 8 | |    |   |   8 |    |   |   8 |    |  |   8      |  |   8   |
        #       | |/ \| |    |   |  /  |    |   |  /  |    |  |  / \     |  |  / \  |
        # 4     | 9  10 |    |   | 9  10    |   | 9  10    |  | 9  10    |  | 9  10 |
        #       |/ \ / \|    |   |  \   \   |   |  \   \   |  |  \   \   |  |  \    |
        # 5     0   1   2    |   0   1   2  |   0   1   2  |  0   1   2  |  0   1   2
        #
        #                    |   0.0 - 0.1  |   0.1 - 0.2  |  0.2 - 0.4  |  0.4 - 0.5
        # ... continued:
        # t                  |             |             |             |
        #
        # 0         --3--    |    --3--    |    --3--    |    --3--    |    --3--
        #          /     \   |   /     \   |   /     \   |   /     \   |   /  |  \
        # 1       4       5  |  4       5  |  4       5  |  4       5  |  4   |   5
        #         |\     /|  |   \     /|  |   \     /|  |   \     /|  |     /   /|
        # 2       | 6   7 |  |    6   7 |  |    6   7 |  |    6   7 |  |    6   7 |
        #         |  \    |  |     \    |  |       /  |  |    |  /  |  |    |  /  |
        # 3  ...  |   8   |  |      8   |  |      8   |  |    | 8   |  |    | 8   |
        #         |  / \  |  |     / \  |  |     / \  |  |    |  \  |  |    |  \  |
        # 4       | 9  10 |  |    9  10 |  |    9  10 |  |    9  10 |  |    9  10 |
        #         |    /  |  |   /   /  |  |   /   /  |  |   /   /  |  |   /   /  |
        # 5       0   1   2  |  0   1   2  |  0   1   2  |  0   1   2  |  0   1   2
        #
        #         0.5 - 0.6  |  0.6 - 0.7  |  0.7 - 0.8  |  0.8 - 0.9  |  0.9 - 1.0

        # divergence betw 0 and 1
        true_diversity_01 = 2*(0.6*4 + 0.2*2 + 0.2*5)
        # divergence betw 1 and 2
        true_diversity_12 = 2*(0.2*5 + 0.2*2 + 0.3*5 + 0.3*4)
        # divergence betw 0 and 2
        true_diversity_02 = 2*(0.2*5 + 0.2*4 + 0.3*5 + 0.1*4 + 0.2*5)
        # mean divergence between 0, 1 and 0, 2
        true_mean_diversity = (
                0 + true_diversity_02 + true_diversity_01 + true_diversity_12) / 4
        # Y(0;1, 2)
        true_Y = 0.2*4 + 0.2*(4+2) + 0.2*4 + 0.2*2 + 0.2*(5+1)

        nodes = six.StringIO("""\
        is_sample       time    population
        1       0.000000        0
        1       0.000000        0
        1       0.000000        0
        0       5.000000        0
        0       4.000000        0
        0       4.000000        0
        0       3.000000        0
        0       3.000000        0
        0       2.000000        0
        0       1.000000        0
        0       1.000000        0
        """)
        edges = six.StringIO("""\
        left    right   parent  child
        0.500000        1.000000        10      1
        0.000000        0.400000        10      2
        0.600000        1.000000        9       0
        0.000000        0.500000        9       1
        0.800000        1.000000        8       10
        0.200000        0.800000        8       9,10
        0.000000        0.200000        8       9
        0.700000        1.000000        7       8
        0.000000        0.200000        7       10
        0.800000        1.000000        6       9
        0.000000        0.700000        6       8
        0.400000        1.000000        5       2,7
        0.100000        0.400000        5       7
        0.600000        0.900000        4       6
        0.000000        0.600000        4       0,6
        0.900000        1.000000        3       4,5,6
        0.100000        0.900000        3       4,5
        0.000000        0.100000        3       4,5,7
        """)
        ts = msprime.load_text(nodes=nodes, edges=edges)
        tsc = msprime.TreeStatCalculator(ts)
        py_tsc = PythonTreeStatCalculator(ts)

        self.check_pairwise_diversity(ts)

        # divergence between 0 and 1
        A = [[0], [1]]

        def f(x):
            return float((x[0] > 0) != (x[1] > 0))/2.0

        # tree lengths:
        self.assertAlmostEqual(py_tsc.tree_length_diversity([0], [1]),
                               true_diversity_01)
        self.assertAlmostEqual(tsc.tree_stat(A, f),
                               true_diversity_01)
        self.assertAlmostEqual(py_tsc.tree_stat(A, f),
                               true_diversity_01)

        # mean divergence between 0, 1 and 0, 2
        A = [[0, 1], [0, 2]]
        n = [len(a) for a in A]

        def f(x):
            return float(x[0]*(n[1]-x[1]) + (n[0]-x[0])*x[1])/8.0

        # tree lengths:
        self.assertAlmostEqual(py_tsc.tree_length_diversity(A[0], A[1]),
                               true_mean_diversity)
        self.assertAlmostEqual(tsc.tree_stat(A, f),
                               true_mean_diversity)
        self.assertAlmostEqual(py_tsc.tree_stat(A, f),
                               true_mean_diversity)

        # Y-statistic for (0/12)
        A = [[0], [1, 2]]

        def f(x):
            return float(((x[0] == 1) and (x[1] == 0)) 
                         or ((x[0] == 0) and (x[1] == 2)))/2.0

        # tree lengths:
        self.assertAlmostEqual(py_tsc.tree_length_Y3([0], [1], [2]), true_Y)
        self.assertAlmostEqual(tsc.tree_stat(A, f), true_Y)
        self.assertAlmostEqual(py_tsc.tree_stat(A, f), true_Y)

    def test_tree_stat_vector_interface(self):
        ts = msprime.simulate(10)
        tsc = msprime.TreeStatCalculator(ts)

        def f(x):
            return [1.0]

        # Duplicated samples raise an error
        self.assertRaises(ValueError, tsc.tree_stat_vector, [[1, 1]], f)
        self.assertRaises(ValueError, tsc.tree_stat_vector, [[1], [2, 2]], f)
        # Make sure the basic call doesn't throw an exception
        tsc.tree_stat_vector([[1, 2]], f)
        # Check for bad windows
        for bad_start in [-1, 1, 1e-7]:
            self.assertRaises(
                ValueError, tsc.tree_stat_vector, [[1, 2]], f,
                [bad_start, ts.sequence_length])
        for bad_end in [0, ts.sequence_length - 1, ts.sequence_length + 1]:
            self.assertRaises(
                ValueError, tsc.tree_stat_vector, [[1, 2]], f,
                [0, bad_end])
        # Windows must be increasing.
        self.assertRaises(
            ValueError, tsc.tree_stat_vector, [[1, 2]], f, [0, 1, 1])


class SiteStatsTestCase(GeneralStatsTestCase):
    """
    Tests of site statistic computation.
    """

    def check_tree_stat_vector(self, ts):
        super().check_tree_stat_vector(ts, calc1=msprime.SiteStatCalculator,
                                       calc2=PythonSiteStatCalculator)

    def check_pairwise_diversity_mutations(self, ts):
        py_tsc = PythonSiteStatCalculator(ts)
        samples = random.sample(ts.samples(), 2)
        A = [[samples[0]], [samples[1]]]
        n = [len(a) for a in A]

        def f(x):
            return float(x[0]*(n[1]-x[1]) + (n[0]-x[0])*x[1])/float(2*n[0]*n[1])

        self.assertAlmostEqual(
                py_tsc.tree_stat(A, f),
                ts.pairwise_diversity(samples=samples))

    def test_pairwise_diversity(self):
        ts = msprime.simulate(20, random_seed=self.random_seed, recombination_rate=100)
        self.check_pairwise_diversity_mutations(ts)

    def test_derived_functions(self):
        # Test implementation of statistics using these functions.
        ts = msprime.simulate(20, random_seed=self.random_seed, recombination_rate=100)
        self.check_tree_stat_vector(ts)
        # self.check_pairwise_diversity(ts)
        # self.check_tmrca_matrix(ts)
        # self.check_f_stats(ts)
        # self.check_Y_stat(ts)

