import unittest

import numpy as np
import librosa
import pytest

from audiomate.corpus import assets

from tests import resources


class TestLabelList(unittest.TestCase):

    def setUp(self):
        file = assets.File('wav', resources.sample_wav_file('wav_1.wav'))
        utt = assets.Utterance('utt', file, start=0.3, end=-1)
        ll = assets.LabelList()
        self.test_label = assets.Label('a', start=0.5, end=-1)
        ll.append(self.test_label)
        utt.set_label_list(ll)

    def test_start_abs(self):
        assert self.test_label.start_abs == pytest.approx(0.8)

    def test_end_abs(self):
        assert self.test_label.end_abs == pytest.approx(2.5951875)

    def test_duration(self):
        assert self.test_label.duration == pytest.approx(1.7951875)

    def test_append(self):
        ll = assets.LabelList()

        label = assets.Label('some text')
        ll.append(label)

        assert len(ll) == 1
        assert label.label_list == ll

    def test_extend(self):
        ll = assets.LabelList()

        label_a = assets.Label('some text')
        label_b = assets.Label('more text')
        label_c = assets.Label('text again')
        ll.extend([label_a, label_b, label_c])

        assert len(ll) == 3
        assert label_a.label_list == ll
        assert label_b.label_list == ll
        assert label_c.label_list == ll

    def test_ranges(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 3.2, 4.5),
            assets.Label('b', 5.1, 8.9),
            assets.Label('c', 7.2, 10.5),
            assets.Label('d', 10.5, 14)
        ])

        ranges = ll.ranges()

        r = next(ranges)
        self.assertEqual(3.2, r[0])
        self.assertEqual(4.5, r[1])
        self.assertIn(ll[0], r[2])

        r = next(ranges)
        self.assertEqual(5.1, r[0])
        self.assertEqual(7.2, r[1])
        self.assertIn(ll[1], r[2])

        r = next(ranges)
        self.assertEqual(7.2, r[0])
        self.assertEqual(8.9, r[1])
        self.assertIn(ll[1], r[2])
        self.assertIn(ll[2], r[2])

        r = next(ranges)
        self.assertEqual(8.9, r[0])
        self.assertEqual(10.5, r[1])
        self.assertIn(ll[2], r[2])

        r = next(ranges)
        self.assertEqual(10.5, r[0])
        self.assertEqual(14, r[1])
        self.assertIn(ll[3], r[2])

        with self.assertRaises(StopIteration):
            next(ranges)

    def test_ranges_with_empty(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 3.2, 4.5),
            assets.Label('b', 5.1, 8.9),
            assets.Label('c', 7.2, 10.5),
            assets.Label('d', 10.5, 14)
        ])

        ranges = ll.ranges(yield_ranges_without_labels=True)

        r = next(ranges)
        self.assertEqual(3.2, r[0])
        self.assertEqual(4.5, r[1])
        self.assertIn(ll[0], r[2])

        r = next(ranges)
        self.assertEqual(4.5, r[0])
        self.assertEqual(5.1, r[1])
        self.assertEqual(0, len(r[2]))

        r = next(ranges)
        self.assertEqual(5.1, r[0])
        self.assertEqual(7.2, r[1])
        self.assertIn(ll[1], r[2])

        r = next(ranges)
        self.assertEqual(7.2, r[0])
        self.assertEqual(8.9, r[1])
        self.assertIn(ll[1], r[2])
        self.assertIn(ll[2], r[2])

        r = next(ranges)
        self.assertEqual(8.9, r[0])
        self.assertEqual(10.5, r[1])
        self.assertIn(ll[2], r[2])

        r = next(ranges)
        self.assertEqual(10.5, r[0])
        self.assertEqual(14, r[1])
        self.assertIn(ll[3], r[2])

        with self.assertRaises(StopIteration):
            next(ranges)

    def test_ranges_include_labels(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 3.2, 4.5),
            assets.Label('b', 5.1, 8.9)
        ])

        ranges = ll.ranges(include_labels=['a'])

        r = next(ranges)
        self.assertEqual(3.2, r[0])
        self.assertEqual(4.5, r[1])
        self.assertIn(ll[0], r[2])

        with self.assertRaises(StopIteration):
            next(ranges)

    def test_ranges_zero_to_end(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 0, -1),
            assets.Label('b', 5.1, 8.9)
        ])

        ranges = ll.ranges()

        r = next(ranges)
        self.assertEqual(0, r[0])
        self.assertEqual(5.1, r[1])
        self.assertIn(ll[0], r[2])

        r = next(ranges)
        self.assertEqual(5.1, r[0])
        self.assertEqual(8.9, r[1])
        self.assertIn(ll[0], r[2])
        self.assertIn(ll[1], r[2])

        r = next(ranges)
        self.assertEqual(8.9, r[0])
        self.assertEqual(-1, r[1])
        self.assertIn(ll[0], r[2])

        with self.assertRaises(StopIteration):
            next(ranges)

    def test_ranges_with_same_start_times(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 1.2, 1.3),
            assets.Label('b', 1.2, 5.6)
        ])

        ranges = ll.ranges()

        r = next(ranges)
        assert r[0] == 1.2
        assert r[1] == 1.3
        assert len(r[2]) == 2
        assert ll[0] in r[2]
        assert ll[1] in r[2]

        r = next(ranges)
        assert r[0] == 1.3
        assert r[1] == 5.6
        assert len(r[2]) == 1
        assert ll[1] in r[2]

        with self.assertRaises(StopIteration):
            next(ranges)

    def test_label_count(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 3.2, 4.5),
            assets.Label('b', 5.1, 8.9),
            assets.Label('c', 7.2, 10.5),
            assets.Label('a', 10.5, 14),
            assets.Label('c', 13, 14)
        ])

        res = ll.label_count()

        self.assertEqual(2, res['a'])
        self.assertEqual(1, res['b'])
        self.assertEqual(2, res['c'])

    def test_label_total_durations(self):
        ll = assets.LabelList(labels=[
            assets.Label('a', 3.2, 4.5),
            assets.Label('b', 5.1, 8.9),
            assets.Label('c', 7.2, 10.5),
            assets.Label('a', 10.5, 14),
            assets.Label('c', 13, 14)
        ])

        res = ll.label_total_duration()

        assert res['a'] == pytest.approx(4.8)
        assert res['b'] == pytest.approx(3.8)
        assert res['c'] == pytest.approx(4.3)

    def test_create_single(self):
        ll = assets.LabelList.create_single('bob')

        assert len(ll) == 1
        assert ll.idx == 'default'
        assert ll[0].value == 'bob'
        assert ll[0].start == 0
        assert ll[0].end == -1

    def test_create_single_with_custom_idx(self):
        ll = assets.LabelList.create_single('bob', idx='name')

        assert len(ll) == 1
        assert ll.idx == 'name'
        assert ll[0].value == 'bob'
        assert ll[0].start == 0
        assert ll[0].end == -1

    def test_split(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 4.0),
            assets.Label('b', 4.0, 8.0),
            assets.Label('c', 9.0, 12.0)
        ])

        res = ll.split([1.9, 6.2, 10.5])

        assert len(res) == 4

        assert len(res[0]) == 1
        assert res[0][0] == assets.Label('a', 0.0, 1.9)

        assert len(res[1]) == 2
        assert res[1][0] == assets.Label('a', 1.9, 4.0)
        assert res[1][1] == assets.Label('b', 4.0, 6.2)

        assert len(res[2]) == 2
        assert res[2][0] == assets.Label('b', 6.2, 8.0)
        assert res[2][1] == assets.Label('c', 9.0, 10.5)

        assert len(res[3]) == 1
        assert res[3][0] == assets.Label('c', 10.5, 12.0)

    def test_split_unsorted_label_list(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 4.0),
            assets.Label('c', 9.0, 12.0),
            assets.Label('b', 4.0, 8.0)
        ])

        res = ll.split([1.9, 6.2, 10.5])

        assert len(res) == 4

        assert len(res[0]) == 1
        assert res[0][0] == assets.Label('a', 0.0, 1.9)

        assert len(res[1]) == 2
        assert res[1][0] == assets.Label('a', 1.9, 4.0)
        assert res[1][1] == assets.Label('b', 4.0, 6.2)

        assert len(res[2]) == 2
        assert res[2][0] == assets.Label('b', 6.2, 8.0)
        assert res[2][1] == assets.Label('c', 9.0, 10.5)

        assert len(res[3]) == 1
        assert res[3][0] == assets.Label('c', 10.5, 12.0)

    def test_split_label_within_cutting_points_is_included(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 4.0),
            assets.Label('b', 4.0, 8.0),
            assets.Label('c', 9.0, 12.0)
        ])

        res = ll.split([1.9, 10.5])

        assert len(res[1]) == 3
        assert res[1][1].value == 'b'
        assert res[1][1].start == 4.0
        assert res[1][1].end == 8.0

    def test_split_with_endless_label(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 4.0),
            assets.Label('c', 4.0, -1)
        ])

        res = ll.split([1.9, 10.5])

        assert len(res) == 3

        assert len(res[2]) == 1
        assert res[2][0].value == 'c'
        assert res[2][0].start == 10.5
        assert res[2][0].end == -1

    def test_split_with_cutting_point_after_last_label(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 4.0),
            assets.Label('c', 4.0, 8.9)
        ])

        res = ll.split([10.5])

        assert len(res) == 2
        assert len(res[0]) == 2
        assert len(res[1]) == 0

    def test_split_cutting_point_on_boundary_doesnot_split_label(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 9.0),
            assets.Label('c', 9.0, 12.0)
        ])

        res = ll.split([9.0])

        assert len(res) == 2

        assert len(res[0]) == 1
        assert len(res[1]) == 1

    def test_split_without_cutting_points_raises_error(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 9.0),
            assets.Label('c', 9.0, 12.0)
        ])

        with pytest.raises(ValueError):
            ll.split([])

    def test_split_with_shifting_start_and_endtime(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 9.0),
            assets.Label('c', 9.0, 12.0)
        ])

        res = ll.split([4.2], shift_times=True)

        assert len(res) == 2

        assert len(res[0]) == 1
        assert res[0][0].value == 'a'
        assert res[0][0].start == 0.0
        assert res[0][0].end == 4.2

        assert len(res[1]) == 2
        assert res[1][0] == assets.Label('a', 0.0, 4.8)
        assert res[1][1] == assets.Label('c', 4.8, 7.8)

    def test_split_first_label_not_splitted(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('a', 0.0, 9.0),
            assets.Label('c', 9.0, 12.0)
        ])

        res = ll.split([11.2], shift_times=True)

        assert len(res) == 2

        assert len(res[0]) == 2
        assert res[0][0] == assets.Label('a', 0.0, 9.0)
        assert res[0][1] == assets.Label('c', 9.0, 11.2)

        assert len(res[1]) == 1
        assert res[1][0] == assets.Label('c', 0.0, pytest.approx(0.8))

    def test_split_single_label_that_doesnt_start_at_zero(self):
        ll = assets.LabelList(idx='test', labels=[
            assets.Label('c', 8.0, 12.0)
        ])

        res = ll.split([11.2], shift_times=True)

        assert len(res) == 2

        assert len(res[0]) == 1
        assert res[0][0] == assets.Label('c', 8.0, 11.2)

        assert len(res[1]) == 1
        assert res[1][0] == assets.Label('c', 0.0, pytest.approx(0.8))


class TestLabel(object):

    def test_label_creation(self):
        a = assets.Label('value', 6.2, 8.9)

        assert a.value == 'value'
        assert a.start == 6.2
        assert a.end == 8.9
        assert len(a.meta) == 0

    def test_label_creation_with_info(self):
        a = assets.Label('value', 6.2, 8.9, meta={'something': 2})

        assert a.value == 'value'
        assert a.start == 6.2
        assert a.end == 8.9
        assert len(a.meta) == 1
        assert a.meta['something'] == 2

    def test_lt_start_time_considered_first(self):
        a = assets.Label('some label', 1.0, 2.0)
        b = assets.Label('some label', 1.1, 2.0)

        assert a < b

    def test_lt_end_time_considered_second(self):
        a = assets.Label('some label', 1.0, 1.9)
        b = assets.Label('some label', 1.0, 2.0)

        assert a < b

    def test_lt_end_time_properly_handles_custom_infinity(self):
        a = assets.Label('some label', 1.0, 1.9)
        b = assets.Label('some label', 1.0, -1)

        assert a < b

    def test_lt_value_considered_third(self):
        a = assets.Label('some label a', 1.0, 2.0)
        b = assets.Label('some label b', 1.0, 2.0)

        assert a < b

    def test_lt_value_ignores_capitalization(self):
        a = assets.Label('some label A', 1.0, 2.0)
        b = assets.Label('some label a', 1.0, 2.0)

        assert not a < b  # not == because == tests different method
        assert not a > b  # not == because == tests different method

    def test_eq_ignores_capitalization(self):
        a = assets.Label('some label A', 1.0, 2.0)
        b = assets.Label('some label a', 1.0, 2.0)

        assert a == b

    def test_eq_ignores_label_list_relation(self):
        a = assets.Label('some label A', 1.0, 2.0)
        b = assets.Label('some label a', 1.0, 2.0)

        al = assets.LabelList(idx='one', labels=[a])
        bl = assets.LabelList(idx='another', labels=[b])

        assert a.label_list == al
        assert b.label_list == bl
        assert a == b

    def test_lt_ignores_label_list_relation(self):
        a = assets.Label('some label A', 1.0, 2.0)
        b = assets.Label('some label a', 1.0, 2.0)

        al = assets.LabelList(idx='one', labels=[a])
        bl = assets.LabelList(idx='another', labels=[b])

        assert a.label_list == al
        assert b.label_list == bl
        assert not a < b
        assert not a > b

    def test_read_samples(self):
        file = assets.File('wav', resources.sample_wav_file('wav_1.wav'))
        issuer = assets.Issuer('toni')
        utt = assets.Utterance('test', file, issuer=issuer, start=1.0, end=2.30)

        l1 = assets.Label('a', 0.15, 0.448)
        l2 = assets.Label('a', 0.5, 0.73)
        ll = assets.LabelList(labels=[l1, l2])

        utt.set_label_list(ll)

        expected, __ = librosa.core.load(file.path, sr=None, offset=1.15, duration=0.298)
        assert np.array_equal(l1.read_samples(), expected)

        expected, __ = librosa.core.load(file.path, sr=None, offset=1.5, duration=0.23)
        assert np.array_equal(l2.read_samples(), expected)

    def test_read_samples_no_utterance_and_label_end(self):
        file = assets.File('wav', resources.sample_wav_file('wav_1.wav'))
        issuer = assets.Issuer('toni')
        utt = assets.Utterance('test', file, issuer=issuer, start=1.0, end=-1)

        l1 = assets.Label('a', 0.15, 0.448)
        l2 = assets.Label('a', 0.5, -1)
        ll = assets.LabelList(labels=[l1, l2])

        utt.set_label_list(ll)

        expected, __ = librosa.core.load(file.path, sr=None, offset=1.15, duration=0.298)
        assert np.array_equal(l1.read_samples(), expected)

        expected, __ = librosa.core.load(file.path, sr=None, offset=1.5)
        assert np.array_equal(l2.read_samples(), expected)

    def test_start_abs(self):
        label = assets.Label('a', 2, 5)
        ll = assets.LabelList(labels=[label])
        assets.Utterance('utt-1', None, start=1, end=19, label_lists=[ll])

        assert label.start_abs == 3

    def test_start_abs_no_utterance(self):
        label = assets.Label('a', 2, 5)

        assert label.start_abs == 2

    def test_end_abs(self):
        label = assets.Label('a', 2, 5)
        ll = assets.LabelList(labels=[label])
        assets.Utterance('utt-1', None, start=1, end=19, label_lists=[ll])

        assert label.end_abs == 6

    def test_end_abs_no_utterance(self):
        label = assets.Label('a', 2, 5)

        assert label.end_abs == 5

    def test_duration(self):
        label = assets.Label('a', 2, 5)

        assert label.duration == 3

    def test_tokenized(self):
        label = assets.Label('wo wie was warum  weshalb')

        assert label.tokenized(delimiter=' ') == ['wo', 'wie', 'was', 'warum', 'weshalb']

    def test_tokenized_returns_empty_list_for_empty_label_value(self):
        label = assets.Label('  ')

        assert label.tokenized(delimiter=' ') == []

    def test_tokenized_with_other_delimiter(self):
        label = assets.Label('wie,kann, ich, dass machen')

        assert label.tokenized(delimiter=',') == ['wie', 'kann', 'ich', 'dass machen']
