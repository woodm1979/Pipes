#!/usr/bin/env python

"""This is a game for playing pipes. :-)"""

import datetime
import optparse
import os
import pygame
import random
from collections import deque

import graphlib
import cevent


PICS_DIR = os.path.join('pics', 'pipes_3D')
PIC_SIZE = 32


class PipeSegment(object):
    """A representation of a segfmfent on the Pipes board."""

    screen = None

    tiles = {}

    min_x = 0
    min_y = 0
    max_x = 0
    max_y = 0

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

    def __init__(self, initial_connections, node):
        """
        Constructor for a pipe segment. seg_type can be:
        'end-cap', 'angle', 'straight', 'tee', or 'cross'.
        """
        for connections in self.initial_end_sets.values():
            if initial_connections in connections:
                self.connections = list(connections)
                break
        else:
            msg = 'Invalid initial_connections: %r' % initial_connections
            raise ValueError(msg)
        self.cursor = self.connections.index(initial_connections)
        self.node = node
        x, y = node
        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)

        self.set_tile_pics()

        self.is_highlighted = False
        self.is_attached = False

    def set_tile_pics(self):
        if self.tiles:
            return

        for major in range(8):
            for minor in range(16):
                pic_file = os.path.join(PICS_DIR, '%03d_%03d.png' % (major,
                                                                     minor))
                self.tiles[(major, minor)] = pygame.image.load(pic_file)

    def on_init(self):
        """
        Jumble the square such that it is random,
        ...but different than initialized.
        """
        if self.is_set():
            return

        possible_cursors = range(len(self.connections))
        possible_cursors.remove(self.cursor)
        self.cursor = random.choice(possible_cursors)

    def rotate_right(self):
        self.cursor += 1
        if self.cursor >= len(self.connections):
            self.cursor = 0

    def rotate_left(self):
        self.cursor -= 1
        if self.cursor < 0:
            self.cursor = len(self.connections) - 1

    def attached_to_source(self):
        """Returns True if self is attached to the source."""
        return self.is_attached

    def is_set(self):
        """Returns True if the segment only has one possibility."""
        return 1 == len(self.connections)

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
        minor = self.set_pic_nums[self.get_connection()]
        return minor

    def get_connection(self):
        return self.connections[self.cursor]

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

    def clone(self):
        new_copy = type(self)(self.get_connection(), self.node)
        return new_copy

    def get_neighbors(self):
        """
        Returns all nodes next to this node.
        NOTE: This includes squares off the board.
        """

        x, y = self.node
        neighbors = [
            (x, y - 1),
            (x + 1, y),
            (x, y + 1),
            (x - 1, y),
        ]
        return neighbors

    def get_possible_connected_nodes(self):
        """
        Returns all possible node-positions that could connect to this node.
        NOTE: This includes squares off the board.
        """
        x, y = self.node
        connected_nodes = deque()
        for direction in self.get_connection():
            if direction == 0:
                connected_nodes.append((x, y - 1))
            elif direction == 1:
                connected_nodes.append((x + 1, y))
            elif direction == 2:
                connected_nodes.append((x, y + 1))
            elif direction == 3:
                connected_nodes.append((x - 1, y))
        return connected_nodes

    def get_links(self, pos):
        sx, sy = self.node
        rx, ry = pos
        dx = sx - rx
        dy = sy - ry

        link_map = {
            (0, 1): (0, 2),
            (0, -1): (2, 0),
            (1, 0): (3, 1),
            (-1, 0): (1, 3),
        }

        return link_map.get((dx, dy))

    def is_connected_to(self, pos):
        links = self.get_links(pos)
        my_link = links[0]
        return my_link in self.get_connection()

    def delete_connection(self, bad_option):
        """Delete any connectfion that contains bad_option."""
        option = self.get_connection()
        for connection in list(self.connections):
            if bad_option in connection:
                self.connections.remove(connection)

        self.cursor = 0
        if option in self.connections:
            self.cursor = self.connections.index(option)

    def is_a_nub(self):
        """
        Returns true if this square will only connect to one other square.
        """
        return len(self.get_connection()) == 1

    def learn_from_neighbor(self, n_square):
        """Returns True if self is modified based on data within neighbor."""
        old_connections = list(self.connections)
        cursor_connection = self.get_connection()
        my_link, his_link = self.get_links(n_square.node)
        his_connections = n_square.connections

        # Check positives first.
        link_missing = False
        for his_connection in his_connections:
            link_missing |= (his_link not in his_connection)
        if not link_missing:
            # Our link MUST be used.
            for my_connection in list(self.connections):
                if my_link not in my_connection:
                    self.connections.remove(my_connection)

        # Check negatives next.
        link_present = False
        for his_connection in his_connections:
            link_present |= (his_link in his_connection)
        if not link_present or (self.is_a_nub() and n_square.is_a_nub()):
            # Our link MUST NOT be used.
            for my_connection in list(self.connections):
                if my_link in my_connection:
                    self.connections.remove(my_connection)

        # If we didn't modify anything, we're done.
        if self.connections == old_connections:
            return False

        # Make sure our cursor isn't pointing to nothing.
        self.cursor = 0
        if cursor_connection in self.connections:
            self.cursor = self.connections.index(cursor_connection)
        return True


class Button(object):
    screen = None

    def __init__(self, call_back, node):
        self.call_back = call_back
        self.node = node

    def press(self, *args, **kwargs):
        self.call_back(*args, **kwargs)

    def on_render(self):
        """Draws the square."""
        major = 2
        minor = 0
        tile = PipeSegment.tiles[(major, minor)]
        x, y = self.node
        self.screen.blit(tile, (PIC_SIZE * x, PIC_SIZE * y))

    def handle_click(self, node):
        if self.pos_in_button(node):
            self.press()

    def pos_in_button(self, pos):
        x, y = pos
        node = (x / PIC_SIZE, y / PIC_SIZE)
        return (node == self.node)


class Solver(object):
    def __init__(self, board):
        self.board = {}

        self.min_x = 0
        self.min_y = 0
        self.max_x = 0
        self.max_y = 0

        for node, square in board.items():
            self.board[node] = square.clone()
            self.board[node].cursor = 0

            x, y = node
            self.min_x = min(self.min_x, x)
            self.max_x = max(self.max_x, x)
            self.min_y = min(self.min_y, y)
            self.max_y = max(self.max_y, y)

    def iter_solved(self):
        for node in self.iter_altered():
            square = self.board[node]
            if square.is_set():
                yield (node, square)

    def iter_altered(self):
        for node in self.solve_edges():
            yield node
        for node in self.solve_all():
            yield node

    def solve_edges(self):
        for node, square in self.board.items():
            x, y = node
            if x == self.min_x:
                square.delete_connection(3)
            if y == self.min_y:
                square.delete_connection(0)
            if x == self.max_x:
                square.delete_connection(1)
            if y == self.max_y:
                square.delete_connection(2)
            if square.is_set():
                yield node

    def solve_all(self):
        altered_something = True
        while altered_something:
            altered_something = False

            num_solved = len(filter(PipeSegment.is_set, self.board.values()))
            print 'num_solved = ' + repr(num_solved)
            if num_solved == len(self.board):
                print 'Solved them all!'
                break

            for node, square in self.board.items():
                altered_this = self.solve_square(square)
                altered_something |= altered_this
                if altered_this:
                    yield node

    def solve_square(self, square):
        modified = False
        if square.is_set():
            return modified
        for n_node in square.get_neighbors():
            try:
                n_square = self.board[n_node]
            except (KeyError, IndexError):
                continue
            modified |= square.learn_from_neighbor(n_square)
        return modified


class PipesBoard(cevent.CEvent):
    """A class representing the game: Pipes!"""

    def __init__(self, columns, rows=None):
        """
        Constructor for PipesBoard; size is either an int or pair of ints.
        """
        x = int(columns)
        y = x
        if rows:
            y = int(rows)

        self.xs = range(x)
        self.ys = range(y)

        self.screen = None
        self.solve_button = None
        self.font = None

        self.board = {}
        self.source = (0, 0)

        self.solver = None
        self.solved = None
        self.ignored_solved = set()

        self._no_clicky = False
        self._is_running = False
        self.start_time = None
        self.finish_time = None

    def on_init(self):
        """Creates the pygame board."""

        self.generate()
        print unicode(self)

        text_height = PIC_SIZE * 2
        width = PIC_SIZE * len(self.xs)
        height = PIC_SIZE * len(self.ys) + text_height

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.font = pygame.font.Font(None, 40)

        PipeSegment.screen = self.screen
        Button.screen = self.screen

        self._is_running = True

        for square in self.board.values():
            square.on_init()

        self.solver = Solver(self.board)
        self.solved = self.solver.iter_solved()
        self.solve_button = Button(self.solve_piece,
                                   (len(self.xs) - 1, len(self.ys) + 1))

        self.start_time = datetime.datetime.now()

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
        for node, links in sorted(graph.nodes.items()):
            connections = []
            sx, sy = node
            for rx, ry in links:
                if sx == rx and sy == ry + 1:
                    connections.append(0)
                elif sx == rx - 1 and sy == ry:
                    connections.append(1)
                elif sx == rx and sy == ry - 1:
                    connections.append(2)
                elif sx == rx + 1 and sy == ry:
                    connections.append(3)

            self.board[node] = PipeSegment(frozenset(connections), node)

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
            if self._no_clicky:
                return
            if event.button == 1:
                self.on_lbutton_up(event)
            elif event.button == 2:
                self.on_mbutton_up(event)
            elif event.button == 3:
                self.on_rbutton_up(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self._no_clicky:
                return
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
        node = (x / PIC_SIZE, y / PIC_SIZE)
        if node not in self.board:
            return None
        return node

    def on_mouse_move(self, event):
        active_node = self._get_node(event.pos)
        for node, square in self.board.items():
            square.is_highlighted = (node == active_node)

    def on_lbutton_down(self, event):
        node = self._get_node(event.pos)
        if node is not None:
            self.board[node].rotate_right()
            return
        self.solve_button.handle_click(event.pos)

    def on_rbutton_down(self, event):
        node = self._get_node(event.pos)
        if node is not None:
            self.board[node].rotate_left()
            return
        self.solve_button.handle_click(event.pos)

    #### Loop ####
    def on_loop(self):
        """Modifies the environment based on signals from events."""
        self.mark_attached()
        self.is_complete()

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

    def is_complete(self):
        for square in self.board.values():
            if not square.is_attached:
                return False
        self._no_clicky = True
        if self.finish_time is None:
            self.finish_time = datetime.datetime.now()
        return True

    #### Render ####
    def on_render(self):
        #self.screen.fill((1, 1, 1))
        self.screen.fill((54, 54, 54))
        for y in self.ys:
            for x in self.xs:
                self.board[(x, y)].on_render()

        self.solve_button.on_render()

        if self._no_clicky:
            self.display_win()
        self.display_time()
        pygame.display.flip()

    def display_win(self):
        text = self.font.render("OMG Kittens!", True, (255, 255, 0))
        text_rect = text.get_rect()
        text_rect.centerx = self.screen.get_rect().centerx
        text_rect.bottom = self.screen.get_rect().bottom - PIC_SIZE
        self.screen.blit(text, text_rect)

    def display_time(self):
        if self.finish_time is None:
            delta = datetime.datetime.now() - self.start_time
        else:
            delta = self.finish_time - self.start_time

        text = str(delta.seconds) + ' sec'
        text = self.font.render(text, True, (255, 255, 0))
        text_rect = text.get_rect()
        text_rect.centerx = self.screen.get_rect().centerx
        text_rect.bottom = self.screen.get_rect().bottom
        self.screen.blit(text, text_rect)

    #### Cleanup ####
    def on_cleanup(self):
        """Clean up the pygame board."""
        pygame.quit()

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

    #### Solving Stuff ####
    def solve_piece(self):
        print 'You cheater!'

        for node in self.ignored_solved:
            k_square = self.solver.board[node]
            known_connection = k_square.get_connection()
            b_square = self.board[node]
            if known_connection != b_square.get_connection():
                self.ignored_solved.remove(node)
                b_square.connections = [known_connection]
                b_square.cursor = 0
                print 'setting %s' % (node, )
                return

        for node, k_square in self.solved:
            known_connection = k_square.get_connection()
            b_square = self.board[node]
            if known_connection == b_square.get_connection():
                self.ignored_solved.add(node)
                continue

            b_square.connections = [known_connection]
            b_square.cursor = 0
            print 'setting %s' % (node, )
            return

        print 'No pieces are known that are not already in place.'
        return


def launch_board(columns=16, rows=None):
    if rows is None:
        rows = columns
    pipes = PipesBoard(columns, rows)
    pipes.on_execute()


def get_command_line_options():
    global PICS_DIR

    parser = optparse.OptionParser()
    parser.add_option('-t', '--tile-directory', dest='tile_directory',
                      help='The directory to find the tile-pngs in.',
                      metavar='DIR', default=PICS_DIR)
    parser.add_option('-r', '--rows', dest='rows',
                      help='The number of rows on the pipes board.',
                      metavar='NUM', default=None)
    parser.add_option('-c', '--columns', dest='columns',
                      help='The number of columns on the pipes board.',
                      metavar='NUM', default=16)

    opts, args = parser.parse_args()

    if opts.rows is None:
        opts.rows = opts.columns

    PICS_DIR = opts.tile_directory

    return opts, args


def main():
    opts, args = get_command_line_options()
    launch_board(opts.columns, opts.rows)


if __name__ == '__main__':
    main()
