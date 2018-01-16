"""
    Find blank pages in documents
"""
import os
from glob import glob
from collections import defaultdict
import json
from bs4 import BeautifulSoup
import re


def load_json(path):
    with open(path, 'r') as f:
        obj = json.load(f)
    return obj


def save_json(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=4, sort_keys=True)


def get_page_summary(summary_path, prefix_len):
    summary = load_json(summary_path)
    page_summaries = summary['page_summaries']
    for i in range(len(page_summaries)):
        page_summaries[i]['text'] = summary['page_texts'][i][:prefix_len].replace('\n', ' ')
    return page_summaries


def get_text(summary_path):
    summary = load_json(summary_path)
    return summary['text']


def get_page_texts(summary_path):
    summary = load_json(summary_path)
    return summary['page_texts']


def base_name(path):
    base = os.path.basename(path)
    return os.path.splitext(base)[0]


def count_same(page_texts, text):
    """`page_texts` is a list of strings that contain `text` as a substring in increasing length
        Returns: Number of items in `page_texts` that are identical to `text`
    """
    for i, t in enumerate(page_texts):
        if t != text:
            assert len(t) > len(text)
            return i
    return len(page_texts)


def find_empty_pages(path, min_len, max_len):
    page_texts = get_page_texts(path)
    page_texts.sort(key=lambda x: (len(x), x))
    page_texts = [text for text in page_texts if min_len <= len(text)]
    if len(page_texts) >= 2:
        for i, text in enumerate(page_texts[:-1]):
            assert len(text) >= min_len
            assert page_texts[i + 1:]
            if len(text) > max_len:
                break
            if all(text in t for t in page_texts[i + 1:]):
                return i, count_same(page_texts, text), len(page_texts), text
    return -1, -1, -1, None


def find_empty_pages_all(root, max_files):
    path_list = list(glob(os.path.join(root, '*.json')))
    if max_files > 0:
        path_list = path_list[:max_files]
    print('%d files' % len(path_list))
    empty_docs = []
    for path in path_list:
        i, m, n, text = find_empty_pages(path, min_len=5, max_len=200)
        if text:
            empty_docs.append((base_name(path), i, m, n, text))
            print(empty_docs[-1])


def summarize_all(root, prefix_len, max_files):
    path_list = list(glob(os.path.join(root, '*.json')))
    if max_files > 0:
        path_list = path_list[:max_files]
    print('%d files' % len(path_list))
    page_summaries = {base_name(path): get_page_summary(path, prefix_len) for path in path_list}
    doc_page = {(name, i): summary
                for name, summaries in page_summaries.items()
                for i, summary in enumerate(summaries)
            }
    page_list = list(doc_page)
    page_list.sort(key=lambda k: (doc_page[k]['n_chars'], doc_page[k]['n_lines'], k))

    def extend_dict(page, info):
        info['_name'] = page[0]
        info['_page'] = page[1]
        return info

    page_info_list = [extend_dict(page, doc_page[page]) for page in page_list]
    save_json('page_info_list.json', page_info_list)

    doc_count = defaultdict(int)
    for i, page in enumerate(page_list):
        doc_count[page[0]] += 1
        if doc_count[page[0]] >= 3:
            continue
        info = doc_page[page]
        print('%6d: %4d l %5d c - %-30s "%s"' % (i, info['n_lines'], info['n_chars'],
            page, info['text']))


RE_TAG = re.compile(r'<.*?>')


def trim(tag):
    i = tag.find(' ')
    if i < 0:
        return tag
    return tag[i]


def find_all_tags(root, do_soup):
    print('=' * 80)
    all_tags = defaultdict(int)
    path_list = list(glob(os.path.join(root, '*.json')))
    for i, path in enumerate(path_list):
        print('%3d: %s %8d' % (i, path, os.path.getsize(path)))
        text = get_text(path)
        if do_soup:
            soup = BeautifulSoup(text, "html5lib")
            for tag in soup.find_all():
                all_tags[tag.name] += 1
        else:
            tags = RE_TAG.findall(text)
            tags = [trim(tag[1:-1]) for tag in tags]
            for tag in tags:
                all_tags[tag] += 1

    print('-' * 80)
    for i, tag in enumerate(sorted(all_tags)):
        print('%3d: %-10s %8d' % (i, tag, all_tags[tag]))


pdf_dir = '~/testdata'
text_dir = '~/testdata.pages0'
pdf_dir = os.path.expanduser(pdf_dir)
text_dir = os.path.expanduser(text_dir)
print('pdf_dir=%s' % pdf_dir)
print('text_dir=%s' % text_dir)


if __name__ == '__main__':
    # summarize_all(text_dir, prefix_len=200, max_files=-1)
    find_empty_pages_all(text_dir, max_files=-1)
    # find_all_tags(text_dir, False)
