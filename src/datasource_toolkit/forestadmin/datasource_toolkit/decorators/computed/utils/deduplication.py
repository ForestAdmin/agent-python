import json
import sys
from typing import Any, Awaitable, Callable, Dict, List

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


Input: TypeAlias = Any
Output: TypeAlias = Any


async def transform_unique_values(inputs: Input, callback: Callable[[List[Input]], Awaitable[List[Output]]]):
    indexes: Dict[int, int] = {}
    mapping: List[int] = []
    unique_inputs: List[Input] = []

    for _input in inputs:
        if _input is not None:
            if isinstance(_input, dict):
                hsh = hash(json.dumps(_input, default=str))
            else:
                hsh = hash(_input)

            if hsh not in indexes:
                indexes[hsh] = len(unique_inputs)
                unique_inputs.append(_input)
            mapping.append(indexes[hsh])
        else:
            mapping.append(-1)

    unique_outputs = await callback(unique_inputs)
    outputs: List[Output] = []

    for idx in mapping:
        if idx != -1:
            outputs.append(unique_outputs[idx])
        else:
            outputs.append(None)

    return outputs
