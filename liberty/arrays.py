##
## Copyright (c) 2019 Thomas Kramer.
## 
## This file is part of liberty-parser 
## (see https://codeberg.org/tok/liberty-parser).
## 
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##
import numpy as np
from typing import List


def array_to_strings(array: np.ndarray) -> List[str]:
    """
    Convert a numpy array into a liberty string format.
    :param array:
    :return:
    """
    array = array.astype(np.float)
    if array.ndim == 1:
        array = [array]
    return [
        ", ".join(("{0:f}".format(x) for x in row))
        for row in array
    ]


def strings_to_array(strings: List[str]) -> np.array:
    """
    Convert liberty string array format in to a numpy array.
    :param strings:
    :return:
    """
    array = [
        np.fromstring(s.replace("\\\n", ""), sep=',')
        for s in strings
    ]
    return np.array(array)


def test_array_to_strings():
    a = np.array([[1, 2, 3], [4, 5, 6]])
    s = array_to_strings(a)
    a2 = strings_to_array(s)

    assert (a == a2).all()
