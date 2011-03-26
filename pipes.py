#!/usr/bin/env python

"""This is a game for playing pipes. :-)"""

import os
import os.path
import pygame
import random
import sys
from collections import deque

import graphlib
import cevent


PICS_DIR = 'pics'
PIC_SIZE = 32


class PipeSegment(object):
    """A representation of a segfment on the Pipes board."""

    screen = None

    tiles = {}
    for major in range(8):
        for minor in range(16):
            pic_file = os.path.join(PICS_DIR, '%03d_%03d.png' % (major, minor))
            tiles[(major, minor)] = pygame.image.load(pic_file)

    initial_end_sets = {
        'end-cap': tuple(map(frozenset, [[0],
                                         [1],
                                         [2],
                                         [3]])),
        'angle': tuple(map(frozenset, [[0, 1],
                                       [1, 2],
                                       [2, 3],
                                       [3, 0]])),
        'straight': tuple(map(frozenset, [[0, 2],
                                          [1, 3]])),
        'tee': tuple(map(frozenset, [[0, 1, 2],
                                     [1, 2, 3],
                                     [2, 3, 0],
                                     [3, 0, 1]])),
        'cross': tuple(map(frozenset, [[0, 1, 2, 3]])),
    }

    set_chars = {
        # End-Caps
        frozenset([0]): u'\u2579',
        frozenset([1]): u'\u257a',
        frozenset([2]): u'\u257b',
        frozenset([3]): u'\u2578',
        # Angles
        frozenset([0, 1]): u'\u255a',
        frozenset([1, 2]): u'\u2554',
        frozenset([2, 3]): u'\u2557',
        frozenset([3, 0]): u'\u255d',
        # Straights
        frozenset([0, 2]): u'\u2551',
        frozenset([1, 3]): u'\u2550',
        # T's
        frozenset([0, 1, 2]): u'\u2560',
        frozenset([1, 2, 3]): u'\u2566',
        frozenset([2, 3, 0]): u'\u2563',
        frozenset([3, 0, 1]): u'\u2569',
        # Crosses
        frozenset([0, 1, 2, 3]): u'\u256c',
    }

    set_pic_nums = {
        # No connection
        frozenset([]): 0,
        # End-Caps
        frozenset([0]): 1,
        frozenset([1]): 2,
        frozenset([2]): 3,
        frozenset([3]): 4,
        # Angles
        frozenset([0, 1]): 7,
        frozenset([1, 2]): 8,
        frozenset([2, 3]): 9,
        frozenset([3, 0]): 10,
        # Straights
        frozenset([0, 2]): 5,
        frozenset([1, 3]): 6,
        # T's
        frozenset([0, 1, 2]): 12,
        frozenset([1, 2, 3]): 13,
        frozenset([2, 3, 0]): 14,
        frozenset([3, 0, 1]): 11,
        # Crosses
        frozenset([0, 1, 2, 3]): 15,
    }

    def __init__(self, seg_type, node):
        """
        Constructor for a pipe segment. seg_type can be:
        'end-cap', 'angle', 'straight', 'tee', or 'cross'.
        """
        self.connections = list(self.initial_end_sets[seg_type])
        self.cursor = random.randrange(len(self.connections))
        self.node = node
        self.is_highlighted = False
        self.is_attached = False

    def rotate_right(self):
        self.cursor += 1
        if self.cursor >= len(self.connections):
            self.cursor = 0

    def rotate_left(self):
        self.cursor -= 1
        if self.cursor < 0:
            self.cursor = len(self.connections) - 1

    def attached_to_source(self):
        return self.is_attached

    def is_set(self):
        """Returns True if the segment only has one possibility."""
        return 1 == len(self.connections)

        return self._hightlighted

    def get_major(self):
        """f
        Returns the tile's major number, which determines which tile-set to
        use.
        """
        major = 0
        if self.attached_to_source():
            major += 1
        if self.is_set():
            major += 2
        if self.is_highlighted:
            major += 4
        return major

    def get_minor(self):
        """
        Returns the tile's minor number, which determines which tile shape to
        use.
        """
        minor = self.set_pic_nums[self.connections[self.cursor]]
        return minor

    def on_render(self):
        """Draws the square."""
        major = self.get_major()
        minor = self.get_minor()
        tile = self.tiles[(major, minor)]
        x, y = self.node
        self.screen.blit(tile, (PIC_SIZE * x, PIC_SIZE * y))

    def __unicode__(self):
        """A unicode representation of a pipe segment."""
        return self.set_chars[self.connections[self.cursor]]

    def get_possible_connected_nodes(self):
        """
        Returns all possible node-positions that could connect to this node.
        NOTE: This can include nodes that don't really connect, and nodes that
              are off the edge of the board.
        """
        x, y = self.node
        connected_nodes = deque()
        for direction in self.connections[self.cursor]:
            if direction == 0:
                connected_nodes.append((x, y - 1))
            elif direction == 1:
                connected_nodes.append((x + 1, y))
            elif direction == 2:
                connected_nodes.append((x, y + 1))
            elif direction == 3:
                connected_nodes.append((x - 1, y))
        return connected_nodes

    def is_connected_to(self, pos):
        sx, sy = self.node
        rx, ry = pos
        dx = sx - rx
        dy = sy - ry

        if dx == 0 and dy == 1:
            return 0 in self.connections[self.cursor]
        if dx == -1 and dy == 0:
            return 1 in self.connections[self.cursor]
        if dx == 0 and dy == -1:
            return 2 in self.connections[self.cursor]
        if dx == 1 and dy == 0:
            return 3 in self.connections[self.cursor]


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


class PipesBoard(cevent.CEvent):
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
        self.source = (0, 0)

        self._is_running = False

    def on_init(self):
        """Creates the pygame board."""
        self.generate()
        print unicode(self)
        size = width, height = PIC_SIZE * len(self.xs), PIC_SIZE * len(self.ys)
        pygame.init()
        self.screen = pygame.display.set_mode(size)
        PipeSegment.screen = self.screen
        self._is_running = True

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

        for node, links in graph.nodes.items():
            if len(links) == 2:
                node_a, node_b = links.keys()
                if node_a[0] == node_b[0] or node_a[1] == node_b[1]:
                    self.board[node] = PipeSegment('straight', node)
                else:
                    self.board[node] = PipeSegment('angle', node)
            else:
                segment_types = {1: 'end-cap', 3: 'tee', 4: 'cross'}
                self.board[node] = PipeSegment(segment_types[len(links)], node)
        self.source = random.choice(self.board.keys())

    def __unicode__(self):
        """A unicode grid of the pipes grid."""
        ret_str = []
        for y in self.ys:
            for x in self.xs:
                ret_str.append(unicode(self.board[(x, y)]))
            ret_str.append(u'\n')

        return u''.join(ret_str)

    #### Events ####
    def on_event(self, event):
        """Reacts to events."""
        if event.type == pygame.QUIT:
            self.on_exit()

        elif event.type >= pygame.USEREVENT:
            self.on_user(event)

        elif event.type == pygame.VIDEOEXPOSE:
            self.on_expose()

        elif event.type == pygame.VIDEORESIZE:
            self.on_resize(event)

        elif event.type == pygame.KEYUP:
            self.on_key_up(event)

        elif event.type == pygame.KEYDOWN:
            self.on_key_down(event)

        elif event.type == pygame.MOUSEMOTION:
            self.on_mouse_move(event)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.on_lbutton_up(event)
            elif event.button == 2:
                self.on_mbutton_up(event)
            elif event.button == 3:
                self.on_rbutton_up(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.on_lbutton_down(event)
            elif event.button == 2:
                self.on_mbutton_down(event)
            elif event.button == 3:
                self.on_rbutton_down(event)

    def on_exit(self):
        self._is_running = False

    def _get_node(self, pos):
        x, y = pos
        return (x / PIC_SIZE, y / PIC_SIZE)

    def on_mouse_move(self, event):
        active_node = self._get_node(event.pos)
        for node, square in self.board.items():
            if node == active_node:
                square.is_highlighted = True
            else:
                square.is_highlighted = False

    def on_lbutton_down(self, event):
        node = self._get_node(event.pos)
        self.board[node].rotate_right()

    def on_rbutton_down(self, event):
        node = self._get_node(event.pos)
        self.board[node].rotate_left()

    #### Loop ####
    def on_loop(self):
        """Modifies the environment based on signals from events."""
        self.mark_attached()

    def mark_attached(self):
        for square in self.board.values():
            square.is_attached = False

        attached_nodes = deque()
        attached_nodes.append(self.source)
        while attached_nodes:
            node = attached_nodes.pop()
            square = self.board.get(node)
            if square is None:
                continue
            if not square.is_attached:
                for potential in square.get_possible_connected_nodes():
                    p_square = self.board.get(potential)
                    if p_square is None:
                        continue
                    if p_square.is_connected_to(node):
                        attached_nodes.append(potential)
            square.is_attached = True

    #### Render ####
    def on_render(self):
        #self.screen.fill((1, 1, 1))
        self.screen.fill((0, 0, 0))
        for y in self.ys:
            for x in self.xs:
                self.board[(x, y)].on_render()
        pygame.display.flip()

    #### Cleanup ####
    def on_cleanup(self):
        """Clean up the pygame board."""
        pygame.quit()

    def neighbor_nodes(self, position, directions):
        """Return the position and segment in the direction of position."""
        if directions is None:
            directions = set(0, 1, 2, 3)
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

    #### Main execution loop ####
    def on_execute(self):
        """Main Execution loop."""
        self.on_init()

        while self._is_running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        self.on_cleanup()


if __name__ == '__main__':

    pipes = PipesBoard(16)
    pipes.on_execute()
