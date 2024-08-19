from lxml import etree

class LuminousHTMLProcessor:
    def __init__(self, html_content, ignore_classes=['twemoji']):
        self.html_content = html_content
        self.ignore_classes = ignore_classes

    def process(self):
        parser = etree.HTMLParser()
        tree = etree.fromstring(self.html_content, parser)

        for element in tree.iter('img'):
            element_classes = element.get('class', '').split()
            if any(ignore_class in element_classes for ignore_class in self.ignore_classes):
                continue

            parent = element.getparent()
            if parent is not None and parent.tag == 'p':
                a = etree.Element('a', {'href': element.get('src'), 'class': 'luminous'})
                element.set('class', 'luminous-target')
                a.append(element)
                parent.append(a)
                if element in parent:
                    parent.remove(element)

        return etree.tostring(tree, encoding='unicode', method='html')