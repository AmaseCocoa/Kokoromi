from bs4 import BeautifulSoup
import lxml

async def autoToc(input):
    soup = BeautifulSoup(input, 'lxml')
    toc_div = soup.find('div', class_='toc')
    if toc_div:
        toc_div.extract()
        aside = soup.new_tag('aside')
        aside.append(toc_div)
        container_div = soup.find('div', class_='container')
        if container_div:
            container_div.append(aside)
    return str(soup)