import re
import codecs
import os
import xml.etree.ElementTree as ET
import sys

'''org example
#+TITLE: ML
#+AUTHOR: YING DAI

* Windows 8 Home
** Windows 8
    this is a note for node above
    this is also a note for node above
** Windows 8
* Windows 8 Enterprise
** Windows RT
*** hh
'''


class Node(object):
    def __init__(self, level, text):
        self.level = level
        self.text = text
        self.children = []
        self.note = r''

    def add_child(self, node):
        self.children.append(node)


class OrgParser(object):
    NODE_RE = re.compile('(?P<level>[*]+)\s+(?P<text>.*)')
    TITLE_RE = re.compile('TITLE\s*:\s+(?P<title>.*)')
    AUTHOR_RE = re.compile('AUTHOR\s*:\s+(?P<author>.*)')
    ROOT_RE = re.compile('ROOT\s*:\s+(?P<root>.*)')

    def __init__(self, org_file):
        self.org_file = org_file
        self.title = ''
        self.author = ''
        self.root_name = ''
        self.nodes = []
        self.prev_node = None
        with codecs.open(org_file, 'r', encoding='UTF-8') as f:
            self.content = f.readlines()

    def parse(self):
        '''parse content line by line
        '''
        prev = None
        for line in self.content:
            line = line.strip()
            if line.startswith('#+'):
                self.handle_meta(line[2:])
            elif line.startswith('*'):
                prev = self.add_node(line)
            else:
                if prev:
                    prev.note += line.strip() + '\n'

    def handle_meta(self, line):
        if line.startswith('AUTHOR'):
            match = self.AUTHOR_RE.search(line)
            if match:
                self.author = match.group('author')
        elif line.startswith('TITLE'):
            match = self.TITLE_RE.search(line)
            if match:
                self.title = match.group('title')
        elif line.startswith('ROOT'):
            match = self.ROOT_RE.search(line)
            if match:
                self.root_name = match.group('root')

    def add_node(self, line):
        match = self.NODE_RE.match(line)
        if match:
            level = match.group('level').count('*')
            text = match.group('text')
            newnode = Node(level=level, text=text)
            if level == 1:
                try:
                    self.nodes[level - 1].append(newnode)
                except IndexError:
                    self.nodes.append([newnode])
            else:
                parent = self.nodes[level - 2][-1]
                parent.add_child(newnode)
                try:
                    self.nodes[level - 1].append(newnode)
                except IndexError:
                    self.nodes.append([newnode])
            return newnode
        else:
            return None

    def to_opml(self):
        '''Export the parsed Node information to OPML format
        '''
        skip_root = False
        if len(self.nodes) == 1:
            self.root_name = self.nodes[0].text
            skip_root = True
        root = ET.Element('opml', attrib={'version': '1.0'})
        head = ET.SubElement(root, 'head')
        title = ET.SubElement(head, 'title')
        title.text = self.title
        author = ET.SubElement(head, 'ownername')
        author.text = self.author
        body = ET.SubElement(root, 'body')
        if not self.root_name:
            self.root_name = title.text
        outline = ET.SubElement(body, 'outline', attrib={
                                'text': self.root_name})

        # Recursively iterate the Node and construct the XML ElementTree
        def iterate_children(node, ol):
            for child in node.children:
                element = ET.SubElement(
                    ol, 'outline', attrib={'text': child.text, '_note': child.note})

                iterate_children(child, element)

        for root_node in self.nodes[0]:
            if not skip_root:
                ol = ET.SubElement(outline, 'outline', attrib={
                                   'text': root_node.text, '_note': root_node.note})
                iterate_children(root_node, ol)
            else:
                iterate_children(root_node, outline)

        opml_file = os.path.splitext(self.org_file)[0] + '.opml'
        # pretty print the xml into the file

        # xmlstr = minidom.parseString(ET.tostring(
        #     root)).toprettyxml(encoding='UTF-8')
        with open(opml_file, 'wb') as f:
            f.write(ET.tostring(root))

        return opml_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: org2opml.py <org file>')
        sys.exit(-1)

    p = OrgParser(sys.argv[1])
    p.parse()
    of = p.to_opml()

    print ('Exporting to OPML<{}> success'.format(of))
