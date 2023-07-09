from dataclasses import dataclass

from .instruction import Instruction
from ..interfaces.execution import ITarget


_cfg = {
    "slots": True,
    "unsafe_hash": True
}


@dataclass(**_cfg)
class _ImportInstruction(Instruction):
    """
    Base instruction for other import instructions.

    Note that the `source` of the import is on the top of the stack.
    """
    inline: bool


@dataclass(**_cfg)
class ImportInto(_ImportInstruction):
    targets: dict[str, ITarget]

    op_code = "import-into"
    operands = ["targets"]


@dataclass(**_cfg)
class Import(_ImportInstruction):
    op_code = "import"


@dataclass(**_cfg)
class ImportAll(_ImportInstruction):
    def __init__(self):
        raise NotImplementedError(f"Star (*) import is not yet supported!")

    op_code = "import-all"
