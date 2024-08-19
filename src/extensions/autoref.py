import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
from urllib.parse import urlparse


class LinkTargetBlankProcessor(Treeprocessor):
    def __init__(self, md, allowed_domains):
        super().__init__(md)
        self.allowed_domains = allowed_domains

    def run(self, root):
        for element in root.iter('a'):
            href = element.get('href', '')
            parsed_url = urlparse(href)

            # Check if the link is not relative and not in the allowed domains
            if parsed_url.netloc and not any(parsed_url.netloc.endswith(domain) for domain in self.allowed_domains):
                element.set('target', '_blank')
                element.set('rel', 'noopener noreferrer')


class LinkTargetBlankExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'allowed_domains': [['example.com'], 'List of allowed domains']
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        allowed_domains = self.getConfig('allowed_domains')
        processor = LinkTargetBlankProcessor(md, allowed_domains)
        md.treeprocessors.register(processor, 'link_target_blank', 15)


def makeExtension(**kwargs):
    return LinkTargetBlankExtension(**kwargs)
