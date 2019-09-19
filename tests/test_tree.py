from segments.tree import Tree
from segments.util import REPLACEMENT_MARKER


def test_error():
    t = Tree(['t', 'o', 'oː'])
    assert t.parse('toːt') == ['t', 'oː', 't']
    assert t.parse('toːt=') == ['t', 'oː', 't', REPLACEMENT_MARKER]
    assert t.parse('toːt=', error=lambda c: '#') == ['t', 'oː', 't', '#']
    assert t.parse('toːt=oː') == ['t', 'oː', 't', REPLACEMENT_MARKER, 'oː']
