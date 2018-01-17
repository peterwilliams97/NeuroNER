"""
    PDF to text conversion
"""
import os
import json
from bs4 import BeautifulSoup
from clean import dehyphenate

# summary=['n_chars', 'n_pages', 'name', 'page_lines', 'page_summaries', 'page_texts', 'pages', 'text']
def update_summary(summary):
    page_texts = []
    page_summaries = []
    page_lines = []
    for page in summary['pages']:
        text = html_to_text(page)
        page_texts.append(text)
        lines = text.split('\n')
        page_lines.append(lines)
        psummary = {
            'n_chars': sum(len(l) for l in lines),
            'n_lines': len(lines),
        }
        page_summaries.append(psummary)

    summary['page_texts'] = page_texts
    summary['page_lines'] = page_lines
    summary['page_summaries'] = page_summaries


def html_to_text(page):
    soup = BeautifulSoup(page, "html5lib")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    text = dehyphenate(text)

    return text


if __name__ == '__main__':
    import sys

    summary_path = sys.argv[1]
    print('summmary_path=%s' % summary_path)

    with open(summary_path, 'r') as f:
        summary = json.load(f)

    update_summary(summary)

    outtemp = '%s.tmp.json' % summary_path
    with open(outtemp, 'w') as f:
        json.dump(summary, f, indent=4, sort_keys=True)
    os.rename(outtemp, summary_path)
