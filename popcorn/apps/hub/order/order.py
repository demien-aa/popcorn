from instruction import Instruction, InstructionType


class Order(object):

    def __init__(self):
        self.instructions = []

    def add_instruction(self, cmd, type=InstructionType.WORKER):
        self.instructions.append(Instruction.create(cmd, type))

    @property
    def empty(self):
        return False if self.instructions else True

    @property
    def length(self):
        return len(self.instructions)
