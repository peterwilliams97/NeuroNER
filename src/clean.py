"""
    PDF to text conversion
"""
import string
import re
from ngrams import Pw


RE_SPACE = re.compile(r'[\t ]+', re.MULTILINE | re.DOTALL)
punctuation = string.punctuation
punctuation = punctuation.replace("-", "")  # don't remove hyphens
RE_BREAK = re.compile(r'(\w+)-([\n\f\r]+)(\w+)([%s]*)\s*' % punctuation,
                      re.MULTILINE | re.DOTALL)

hyphenated = set()


def unbreak(m):
    global hyphenated

    w00 = m.group(0)
    w0 = m.group(1) + '-' + m.group(2) + m.group(3)
    w1 = m.group(1) + '-' + m.group(3)
    w2 = m.group(1) + m.group(3)
    w1n = w1 + m.group(4) + '\n'
    w2n = w2 + m.group(4) + '\n'
    p0 = Pw(w0)
    p1 = Pw(w1)
    p2 = Pw(w1)
    if p1 < 1e-32 and p2 < 1e-34:
        p1a = Pw(m.group(1)) * Pw(m.group(3))
        if p1a > 1e-27:
            p1 = p1a
    probs = [(p, i) for i, p in enumerate([p0, p1, p2])]
    words = [w00, w1n, w2n]
    _, best = max(probs)

    # assert m.group(1) != 'indi' or words[best] == 'individual\n', '"%s" %s %s %s "%s"' % (
    #                        m.group(0), m.groups(), [p0, p1, p2],
    #                        best, words[best])

    if best != 2:
        hyphenated.add((w1, w2))
    return words[best]


def dehyphenate(text):
    """
        The businesses around newspapers, books, and mag-
        azines are changing on a daily basis; even still, global electronic com-
        munication over the Internet
     =>
        The businesses around newspapers, books, and magazines
        are changing on a daily basis; even still, global electronic communication
        over the Internet
    """
    assert isinstance(text, str), type(text)
    # print([type(x) for x in (text, RE_BREAK, unbreak)])
    unbroke = RE_BREAK.sub(unbreak, text)
    return unbroke


