#!/usr/bin/env python

"""This is a game for playing pipes. :-)"""

import pygame
import random

import graphlib


class PipeSegment(object):
    """A representation of a segment on the Pipes board."""

    initial_end_sets = {
        'end-cap': frozenset(map(frozenset, [[0], [1], [2], [3]])),
        'angle': frozenset(map(frozenset, [[0, 1], [1, 2], [2, 3], [3, 0]])),
        'straight': frozenset(map(frozenset, [[0, 2], [1, 3]])),
        'tee': frozenset(map(frozenset, [[0, 1, 2], [1, 2, 3],
                                         [2, 3, 0], [3, 0, 1]])),
        'cross': frozenset(map(frozenset, [[0, 1, 2, 3]])),
    }

    unset_chars = {
        # End-Caps
        frozenset([0]): u'\u2579', frozenset([1]): u'\u257a',
        frozenset([2]): u'\u257b', frozenset([3]): u'\u2578',
        # Angles
        frozenset([0, 1]): u'\u2517', frozenset([1, 2]): u'\u250f',
        frozenset([2, 3]): u'\u2513', frozenset([3, 0]): u'\u251b',
        # Straights
        frozenset([0, 2]): u'\u2503', frozenset([1, 3]): u'\u2501',
        # T's
        frozenset([0, 1, 2]): u'\u2523', frozenset([1, 2, 3]): u'\u2533',
        frozenset([2, 3, 0]): u'\u252b', frozenset([3, 0, 1]): u'\u253b',
        # Crosses
        frozenset([0, 1, 2, 3]): u'\u254b',
    }

    set_chars = {
        # End-Caps
        frozenset([0]): u'\u2579', frozenset([1]): u'\u257a',
        frozenset([2]): u'\u257b', frozenset([3]): u'\u2578',
        # Angles
        frozenset([0, 1]): u'\u255a', frozenset([1, 2]): u'\u2554',
        frozenset([2, 3]): u'\u2557', frozenset([3, 0]): u'\u255d',
        # Straights
        frozenset([0, 2]): u'\u2551', frozenset([1, 3]): u'\u2550',
        # T's
        frozenset([0, 1, 2]): u'\u2560', frozenset([1, 2, 3]): u'\u2566',
        frozenset([2, 3, 0]): u'\u2563', frozenset([3, 0, 1]): u'\u2569',
        # Crosses
        frozenset([0, 1, 2, 3]): u'\u256c',
    }

    def __init__(self, seg_type):
        """
        Constructor for a pipe segment. seg_type can be:
        'end-cap', 'angle', 'straight', 'tee', or 'cross'.
        """
        self.connections = set(self.initial_end_sets[seg_type])

    def is_set(self):
        """Returns True if the segment only has one possibility."""
        return 1 == len(self.connections)

    def __unicode__(self):
        """A unicode representation of a pipe segment."""
        if self.is_set():
            return self.set_chars[iter(self.connections).next()]
        else:
            return self.unset_chars[iter(self.connections).next()]

    def delete_connection(self, bad_option):
        """Delete any connection that contains bad_option."""
        for connection in self.connections:
            if bad_option in connection:
                self.connections -= bad_option

    def require_connection(self, needed_option):
        """Delete any connection that doesn't contain needed_option."""
        for connection in self.connections:
            if needed_option not in connection:
                self.connections -= connection

    def get_good_connections(self):
        """Return any connection that's absolutely required by self."""
        good_connections = set((0, 1, 2, 3))
        for connection in self.connections:
            good_connections &= connection
        return good_connections

    def get_bad_connections(self):
        """Return any connection that absolutely can not attach to self."""
        bad_connections = set((0, 1, 2, 3))
        for connection in self.connections:
            bad_connections -= connection
        return bad_connections


class PipesBoard(object):
    """A class representing the game: Pipes!"""

    def __init__(self, size):
        """
        Constructor for PipesBoard; size is either an int or pair of ints.
        """
        try:
            x = int(size)
            y = int(size)
        except TypeError:
            x, y = size

        self.xs = range(x)
        self.ys = range(y)

        self.board = {}
        self.generate()

    def generate(self):
        """Generate a starting Pipes setup."""

        graph = graphlib.UndirectedGraph()
        for x in self.xs:
            for y in self.ys:
                if x != 0:
                    graph.create_edge((x, y), (x - 1, y), random.random())
                if y != 0:
                    graph.create_edge((x, y), (x, y - 1), random.random())

        graph = graph.min_span_tree()

        for node, links in graph.nodes.iteritems():
            if len(links) == 2:
                node_a, node_b = links.keys()
                if node_a[0] == node_b[0] or node_a[1] == node_b[1]:
                    self.board[node] = PipeSegment('straight')
                else:
                    self.board[node] = PipeSegment('angle')
            else:
                segment_types = {1: 'end-cap', 3: 'tee', 4: 'cross'}
                self.board[node] = PipeSegment(segment_types[len(links)])

    def __unicode__(self):
        """A unicode grid of the pipes grid."""
        ret_str = []
        for y in self.ys:
            for x in self.xs:
                ret_str.append(unicode(self.board[(x, y)]))
            ret_str.append(u'\n')

        return u''.join(ret_str)

    def neighbor_nodes(self, position, directions):
        """Return the position and segment in the direction of position."""
        if directions is None:
            directions = set(0, 1, 2, 3)
        pass
        # FIXME Here's where you start.

    def solve(self):
        """Attempt to solve the Pipes game."""

        # clean up the edges.
        self._solve_edges()

        # Keep a queue of pieces to look at.
        to_be_checked = set(position for position, segment
                            in self.board.iteritems if segment.is_set())

        while to_be_checked:
            position = to_be_checked.pop()
            segment = self.board[position]

            bad_connections = segment.get_bad_connections
            good_connections = segment.get_good_connections

    def _solve_edges(self):
        for position, segment in self.board:
            print 'position = ' + repr(position)
            print 'segment = ' + repr(segment)
            if position[0] == self.xs[0]:
                segment.delete_connection(3)
            if position[1] == self.ys[0]:
                segment.delete_connection(0)
            if position[0] == self.xs[-1]:
                segment.delete_connection(1)
            if position[1] == self.ys[-1]:
                segment.delete_connection(2)


if __name__ == '__main__':
    board = PipesBoard(4)
    print unicode(board)
    print
    board.solve()
    print unicode(board)
