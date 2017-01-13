from __future__ import unicode_literals, print_function
import sys


class TreeNode(object):
    """
    Private class that creates the tree data structure from the orthography profile for
    parsing.
    """

    def __init__(self, char, sentinel=False):
        self.char = char
        self.children = {}
        self.sentinel = sentinel


class Tree(object):
    def __init__(self, token_list):
        # Internal function to add a multigraph starting at node.
        def addMultigraph(node, line):
            for char in line:
                node = node.children.setdefault(char, TreeNode(char))
            node.sentinel = True

        # Add all multigraphs in each line of file_name.
        # Skip "#" comments and blank lines.
        self.root = TreeNode('', sentinel=True)

        for tokens in token_list:
            addMultigraph(self.root, tokens[0])

    def parse(self, line):
        parse = self._parse(self.root, line)
        return "# " + parse if parse else ""

    def _parse(self, root, line, idx=0):
        # Base (or degenerate..) case.
        if len(line) == 0:
            return "#"

        parse = ""
        curr = 0
        node = root
        while curr < len(line):
            node = node.children.get(line[curr])
            curr += 1
            if not node:
                break
            if node.sentinel:
                subparse = self._parse(root, line[curr:], idx=curr)
                if len(subparse) > 0:
                    # Always keep the latest valid parse, which will be
                    # the longest-matched (greedy match) graphemes.
                    parse = line[:curr] + " " + subparse
        return parse

    def printTree(self, root, path='', stream=sys.stdout):
        for char, child in root.children.items():
            if child.sentinel:
                char += "*"
            branch = " -- " if len(path) > 0 else ""
            self.printTree(child, path + branch + char, stream=stream)
        if not root.children:
            print(path, file=stream)


def printMultigraphs(root, line, result):
    # Base (or degenerate..) case.
    if len(line) == 0:
        result += "#"
        return result

    # Walk until we run out of either nodes or characters.
    curr = 0   # Current index in line.
    last = 0   # Index of last character of last-seen multigraph.
    node = root
    while curr < len(line):
        node = node.children.get(line[curr])
        if not node:
            break
        if node.sentinel:
            last = curr
        curr += 1

    # Print everything up to the last-seen sentinel, and process
    # the rest of the line, while there is any remaining.
    last = last + 1  # End of span (noninclusive).
    result += line[:last] + " "
    return printMultigraphs(root, line[last:], result)
