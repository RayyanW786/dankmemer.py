from typing import Optional, Union, Tuple, Dict, Any
from .utils import Fuzzy, IN, Above, Below, Range

StringFilterType = Optional[Union[str, Fuzzy, IN]]

NumericFilterType = Optional[
    Union[
        int,
        float,
        Tuple[Union[int, float], Union[int, float]],
        Above,
        Below,
        Range
    ]
]

StringType = Optional[str]

BooleanType = Optional[bool]

IntegerType = Optional[int]

DictType = Optional[Dict[str, Any]]
