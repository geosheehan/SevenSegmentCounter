
import time

import board
from digitalio import DigitalInOut, Direction, Pull


class Digit(object):
    # Constant values
    _7_segment_index = [
        0x3f,   # 0
        0x06,   # 1
        0x5b,   # 2
        0x4f,   # 3
        0x66,   # 4
        0x6d,   # 5
        0x7d,   # 6
        0x07,   # 7
        0x7f,   # 8
        0x6f    # 9
    ]

    def __init__(self):
        self.__index = 8

    def __str__(self):
        segment_value = self._7_segment_index[self.__index]
        return "{:07b}".format(segment_value)

    def increment(self, amount=1):
        new_index = (self.__index + amount)
        self.__index = new_index % len(self._7_segment_index)
        did_wrap = new_index != self.__index
        return did_wrap

    def reset(self):
        self.__index = 0


class Number(object):
    def __init__(self, num_digits=2):
        self.size = num_digits
        self.__digits = [Digit() for _ in range(num_digits)]

    def __str__(self):
        out = ""
        for digit in self.__digits:
            out += "{}".format(digit)
        return out

    def increment(self, amount=1):
        index = 0
        has_wrapped = True
        while has_wrapped and index < len(self.__digits):
            has_wrapped = self.__digits[index].increment(amount)
            index += 1

    def decrement(self, amount=-1):
        self.increment(amount)

    def reset(self):
        for digit in self.__digits:
            digit.reset()


class SegmentDescriptor(object):
    def __init__(self, index):
        self.index = index

    def __get__(self, instance, owner):
        return instance.segments[self.index]

    def __set__(self, instance, value):
        instance.segments[self.index] = value


class Segment(object):
    def __init__(self):
        self.value = False


class SevenSegmentDigit(object):
    def __init__(self, output):
        # A - G
        if not output:
            self.segments = [Segment() for _ in range(7)]
        else:
            self.segments = [DigitalInOut(out) for out in output]
            for segment in self.segments:
                segment.direction = Direction.OUTPUT

        for i in range(len(self.segments)):
            setattr(type(self), chr(97 + i), SegmentDescriptor(i))

    def set_segments(self, string):
        for index, char in enumerate(reversed(string)):
            self.segments[index].value = bool(int(char))


class Display(object):
    def __init__(self, outputs):
        self.__digits = [SevenSegmentDigit(output) for output in outputs]

    @staticmethod
    def __bar(digits, index):
        out = ""
        for digit in digits:
            segment = digit[index]
            top = "_" if segment.value else " "
            out += " {}  ".format(top)
        return out

    def __side(self, digits, i):
        out = ""
        for digit in digits:
            out += self.__side_seg(digit, i)
            out += self.__side_seg(digit, i + 1)
        return out

    @staticmethod
    def __side_seg(digit, i):
        out = ""
        segment = digit[i]
        bar = "|" if segment.value else " "
        out += "{} ".format(bar)
        return out

    def __fill(self, digits):
        out = ""
        offset = 0
        for index in range(5):
            if not (index % 2):
                out += self.__bar(digits, index + offset)
            else:
                out += self.__side(digits, index + offset)
                offset += 1
            out += "\n"
        return out

    def __str__(self):
        digits = reversed(self.__digits)
        segments = []
        for d in digits:
            segments.append([d.a, d.f, d.b, d.g, d.e, d.c, d.d])
        return self.__fill(segments)

    def show(self, number):
        string = str(number)
        n = 7
        split_string = [string[i:i + n] for i in range(0, len(string), n)]
        for s, digit in zip(split_string, self.__digits):
            digit.set_segments(s)


class Button(object):
    def __init__(self, pin):
        self.__input = DigitalInOut(pin)
        self.__input.direction = Direction.INPUT
        self.__input.pull = Pull.UP
        self.__cur_state = None
        self.__prev_state = None

    @property
    def value(self):
        self.__prev_state = self.__cur_state
        self.__cur_state = self.__input.value
        return self.__cur_state

    def state_changed(self):
        has_changed = self.__prev_state != self.__cur_state
        self.__prev_state = self.__cur_state
        return has_changed


num = Number()

# Inputs
button_up = Button(board.D11)
button_down = Button(board.D12)
button_reset = Button(board.D13)

# Outputs
ones_segments = [
    board.MISO,     # H
    board.RX,       # I
    board.TX,       # J
    board.D5,       # K
    board.D6,       # L
    board.D9,       # M
    board.D10       # N
]
tens_segments = [
    board.A1,       # A
    board.A2,       # B
    board.A3,       # C
    board.A4,       # D
    board.A5,       # E
    board.SCK,      # F
    board.MOSI,     # G
]
display = Display([ones_segments, tens_segments])

command = ''
changed = True
while True:
    global changed
    if not button_up.value and button_up.state_changed():
        num.increment()
        changed = True
    elif not button_down.value and button_down.state_changed():
        num.decrement()
        changed = True
    elif not button_reset.value and button_reset.state_changed():
        num.reset()
        changed = True

    if changed:
        display.show(num)
        print(display)
        changed = False

    time.sleep(0.01)
