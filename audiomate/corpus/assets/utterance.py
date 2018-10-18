import collections

import numpy as np

from audiomate.utils import units
from . import label


class Utterance(object):
    """
    An utterance defines a sample of audio. It is part of a file or can span over the whole file.

    Args:
        idx (str): A unique identifier for the utterance within a dataset.
        file (File): The file this utterance is belonging to.
        issuer (Issuer): The issuer this utterance was created from.
        start (float): The start of the utterance within the audio file in seconds. (default 0)
        end (float): The end of the utterance within the audio file in seconds. -1 indicates that
                     the utterance ends at the end of the file. (default -1)
        label_lists (LabelList, list): A single or multiple label-lists.

    Attributes:
        label_lists (dict): A dictionary containing label-lists with the label-list-idx as key.
    """

    __slots__ = ['idx', 'file', 'issuer', 'start', 'end', 'label_lists']

    def __init__(self, idx, file, issuer=None, start=0, end=-1, label_lists=None):
        self.idx = idx
        self.file = file
        self.issuer = issuer
        self.start = start
        self.end = end
        self.label_lists = {}

        if label_lists is not None:
            self.set_label_list(label_lists)

        if self.issuer is not None:
            self.issuer.utterances.add(self)

    @property
    def end_abs(self):
        """
        Return the absolute end of the utterance relative to the signal.
        """
        if self.end == -1:
            return self.file.duration
        else:
            return self.end

    @property
    def duration(self):
        """
        Return the absolute duration in seconds.
        """
        return self.end_abs - self.start

    def num_samples(self, sr=None):
        """
        Return the number of samples.

        Args:
            sr (int): Calculate the number of samples with the given sampling-rate.
                      If None use the native sampling-rate.

        Returns:
            int: Number of samples
        """
        native_sr = self.sampling_rate
        num_samples = units.seconds_to_sample(self.duration, native_sr)

        if sr is not None:
            ratio = float(sr) / native_sr
            num_samples = int(np.ceil(num_samples * ratio))

        return num_samples

    #
    #   Signal
    #

    def read_samples(self, sr=None, offset=0, duration=None):
        """
        Read the samples of the utterance.

        Args:
            sr (int): If None uses the sampling rate given by the file, otherwise resamples to the given sampling rate.
            offset (float): Offset in seconds to read samples from.
            duration (float): If not None read only this number of seconds in maximum.

        Returns:
            np.ndarray: A numpy array containing the samples as a floating point (numpy.float32) time series.
        """

        read_duration = None

        if self.end >= 0:
            read_duration = self.duration

        if offset > 0:
            read_duration -= offset

        if duration is not None:
            read_duration = min(duration, read_duration)

        return self.file.read_samples(sr=sr, offset=self.start + offset, duration=read_duration)

    @property
    def sampling_rate(self):
        """
        Return the sampling rate.
        """
        return self.file.sampling_rate

    #
    #   Labels
    #

    def set_label_list(self, label_lists):
        """
        Set the given label-list for this utterance. If the label-list-idx is not set, ``default`` is used.
        If there is already a label-list with the given idx, it will be overriden.

        Args:
            label_list (LabelList, list): A single or multiple label-lists to add.

        """

        if isinstance(label_lists, label.LabelList):
            label_lists = [label_lists]

        for label_list in label_lists:
            if label_list.idx is None:
                label_list.idx = 'default'

            label_list.utterance = self
            self.label_lists[label_list.idx] = label_list

    def all_label_values(self, label_list_ids=None):
        """
        Return a set of all label-values occurring in this utterance.

        Args:
            label_list_ids (list): If not None, only label-values from label-lists with an id contained in this list
                                   are considered.

        Returns:
             :class:`set`: A set of distinct label-values.
        """
        values = set()

        for label_list in self.label_lists.values():
            if label_list_ids is None or label_list.idx in label_list_ids:
                values = values.union(label_list.label_values())

        return values

    def label_count(self, label_list_ids=None):
        """
        Return a dictionary containing the number of times, every label-value in this utterance is occurring.

        Args:
            label_list_ids (list): If not None, only labels from label-lists with an id contained in this list
                                   are considered.

        Returns:
            dict: A dictionary containing the number of occurrences with the label-value as key.
        """
        count = collections.defaultdict(int)

        for label_list in self.label_lists.values():
            if label_list_ids is None or label_list.idx in label_list_ids:
                for label_value, label_count in label_list.label_count().items():
                    count[label_value] += label_count

        return count

    def all_tokens(self, delimiter=' ', label_list_ids=None):
        """
        Return a list of all tokens occurring in one of the labels in the label-lists.

        Args:
            delimiter (str): The delimiter used to split labels into tokens
                             (see :meth:`audiomate.corpus.assets.Label.tokenized`).
            label_list_ids (list): If not None, only labels from label-lists with an idx contained in this list
                                   are considered.

        Returns:
             :class:`set`: A set of distinct tokens.
        """
        tokens = set()

        for label_list in self.label_lists.values():
            if label_list_ids is None or label_list.idx in label_list_ids:
                tokens = tokens.union(label_list.all_tokens(delimiter=delimiter))

        return tokens

    def label_total_duration(self, label_list_ids=None):
        """
        Return a dictionary containing the number of seconds, every label-value is occurring in this utterance.

        Args:
            label_list_ids (list): If not None, only labels from label-lists with an id contained in this list
                                   are considered.

        Returns:
            dict: A dictionary containing the number of seconds with the label-value as key.
        """
        duration = collections.defaultdict(float)

        for label_list in self.label_lists.values():
            if label_list_ids is None or label_list.idx in label_list_ids:
                for label_value, label_duration in label_list.label_total_duration().items():
                    duration[label_value] += label_duration

        return duration

    def split(self, cutting_points, file_relative=False):
        """
        Split the utterance into x parts (sub-utterances) and return them as new utterances.
        x is defined by cutting_points (``x = len(cutting_points) + 1``).

        By default cutting-points are relative to the start of the utterance.
        For example if an utterance starts at 50s,
        a cutting-point of 10.0 will split the utterance at 60s relative to the file.

        Args:
            cutting_points (list): List of floats defining the times in seconds where to split the utterance.
            file_relative (bool): If True, cutting-points are relative to the start of the file.
                                  Otherwise they are relative to the start of the utterance.

        Returns:
            list: List of :class:`Utterance`'s.

        Example:

            >>> utt = Utterance('utt-1', 'file-x', start=0.0, end=30.0)
            >>> sub_utts = utt.split([10.0, 20.0])
            >>> len(sub_utts)
            3
            >>> sub_utts[0].start
            0.0
            >>> sub_utts[0].end
            10.0
        """

        if not file_relative:
            cutting_points = [c + self.start for c in cutting_points]

        if len(cutting_points) == 0:
            raise ValueError('At least 1 cutting point is needed!')

        splitted_label_lists = collections.defaultdict(list)

        for idx, label_list in self.label_lists.items():
            label_cutting_points = [x - self.start for x in cutting_points]
            parts = label_list.split(label_cutting_points, shift_times=True)
            splitted_label_lists[idx] = parts

        filtered_cutting_points = []

        for cutting_point in cutting_points:
            if cutting_point > self.start and (cutting_point < self.end or self.end < 0):
                filtered_cutting_points.append(cutting_point)

        sub_utterances = []

        for index in range(len(filtered_cutting_points) + 1):
            if index == 0:
                sub_start = self.start
            else:
                sub_start = cutting_points[index - 1]

            if index >= len(filtered_cutting_points):
                sub_end = self.end
            else:
                sub_end = filtered_cutting_points[index]

            new_idx = '{}_{}'.format(self.idx, index)
            new_utt = Utterance(new_idx, file=self.file, issuer=self.issuer, start=sub_start, end=sub_end)

            for parts in splitted_label_lists.values():
                new_utt.set_label_list(parts[index])

            sub_utterances.append(new_utt)

        return sub_utterances
