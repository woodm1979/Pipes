#!/usr/bin/env python

"""
A module for manipulating and analyzing graphs in python.

NOTE: Please don't use this for anything important.  Use networkx
"""

import heapq


##############
# Exceptions #
##############
class GraphLookupError(LookupError):
    """Lookup errors in Graphs."""
    pass


class InvalidGraphError(TypeError):
    """Invalid Graph error."""
    pass


#################
# Graph objects #
#################
class DirectedGraph(object):
    """A directed graph."""

    def __init__(self):
        """Creates a blank graph with no nodes or edges."""
        self.nodes = {}

    def create_node(self, node_name):
        """Create a node within the graph."""
        self.nodes.setdefault(node_name, {})

    def create_edge(self, node_a, node_b, weight=1):
        """
        Create a directed (one way) edge between two nodes with weight,
        weight.
        """
        self.create_node(node_a)
        self.create_node(node_b)
        self.nodes[node_a][node_b] = weight

    def __len__(self):
        """The number of nodes in the graph."""
        return len(self.nodes)

    def __str__(self):
        """String representation of a graph."""
        ret_str = ["Nodes:"]
        for node, edges in sorted(self.nodes.items()):
            ret_str.append("    %s : %s" % (node, edges))
        return '\n'.join(ret_str)

    def breadth_first_search(self, start_node, end_node):
        """
        Returns a (not the) shortest path between start_node and end_node.

        Ignores edge weighting (treats all edges as weight=1), we're just
        looking for hop-count here.

        If there's no path between node_a and node_b, raise a
        GraphLookupError.
        If start_node or end_node are not nodes on the graph, raise a
        KeyError.
        """

        if start_node not in self.nodes:
            raise KeyError("%s isn't a node in this graph." % (start_node,))

        if end_node not in self.nodes:
            raise KeyError("%s isn't a node in this graph." % (end_node,))

        n_distance = {start_node: 0}
        n_parent = {start_node: None}
        #n_color = {}
        #for node in self.nodes:
        #    n_color[node] = 0
        #n_color[start_node] = 1

        queue = [start_node]
        while queue:
            node = queue.pop(0)
            if node == end_node:
                node_path = [end_node]
                while node_path[-1] != start_node:
                    node_path.append(n_parent[node_path[-1]])

                return reversed(node_path)

            for adj_node in self.nodes[node]:
                #if not n_color[adj_node]:
                if not adj_node in n_distance:
                    #n_color[adj_node] = 1
                    n_distance[adj_node] = n_distance[node] + 1
                    n_parent[adj_node] = node
                    queue.append(adj_node)

        # We've found all nodes connected to start_node, and none of them
        # were end_node.
        raise GraphLookupError("%s and %s are not connected." %
                               (start_node, end_node))

    def shortest_path_found(self, start_node, end_node):
        """
        Returns a (not the) shortest path between start_node and end_node.

        Unlike breadth_first_search, this function takes into account edge
        weights.

        If there's no path between start_node and end_node, raise a
        GraphLookupError.
        If start_node or end_node are not nodes on the graph, raise a
        KeyError.
        """

        if start_node not in self.nodes:
            raise KeyError("%s isn't a node in this graph." % (start_node,))

        if end_node not in self.nodes:
            raise KeyError("%s isn't a node in this graph." % (end_node,))

        n_distance = {}
        n_parent = {}
        queue = [(0, start_node, None)]
        while queue:
            distance, cursor_node, parent_node = heapq.heappop(queue)

            if cursor_node in n_parent:
                continue

            n_distance[cursor_node] = distance
            n_parent[cursor_node] = parent_node

            if cursor_node == end_node:
                node_path = [end_node]
                while node_path[-1] != start_node:
                    node_path.append(n_parent[node_path[-1]])

                return (distance, reversed(node_path))

            for adj_node, adj_distance in self.nodes[cursor_node].items():
                if adj_node not in n_parent:
                    heapq.heappush(queue,
                        (distance + adj_distance, adj_node, cursor_node))

        # All nodes connected to start_node have been searched, and end_node
        # was not hit.
        raise GraphLookupError("%s and %s are not connected." %
                               (repr(start_node), repr(end_node)))


class UndirectedGraph(DirectedGraph):
    """A directed graph."""

    def create_edge(self, node_a, node_b, weight=1):
        """
        Create an undirected (two way) edge between two nodes with weight,
        weight.
        """

        DirectedGraph.create_edge(self, node_a, node_b, weight)
        DirectedGraph.create_edge(self, node_b, node_a, weight)

    def min_span_tree_kruskal(self):
        """
        Find the minimum weighted tree which completely spans the graph.
        Uses Kruskal's algorithm. (Cormen, Chapt 24.2)
        """

        # Create a new graph to keep track of the min_span_tree.
        mst = type(self)()

        # sets: a dict of seperate units.
        sets = dict((node, set([node])) for node in self.nodes)

        # edges: a list of edges sorted by weight.
        edges = sorted((weight, (node_a, node_b))
                       for node_a, value in self.nodes.items()
                       for node_b, weight in value.items())

        # Walk the list of edges, small to large.
        for (weight, (node_a, node_b)) in edges:
            if sets[node_a] != sets[node_b]:
                # Create the edge
                mst.create_edge(node_a, node_b, weight)

                # Combine the two sets.
                set_a, set_b = sorted((sets[node_a], sets[node_b]), key=len)
                set_b |= set_a
                for node in set_a:
                    sets[node] = set_b

                # Check to see if we're done.
                #if len(mst) == len(sets):
                if len(set_b) == len(sets):
                    return mst

        else:
            raise InvalidGraphError(
                    "Minimum spanning tree not possible. Graph not connected.")

    min_span_tree = min_span_tree_kruskal
