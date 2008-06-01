import lz
import misc

debug = False


class compress(lz.compress):
    def __init__(self, data):
        lz.compress.__init__(self, 2)
        self.data = data
        self.compressed = ""
        self.bzoffset = 0

    def __literal(self):
        if debug: print "blz: literal {", \
            self.bzoffset, self.data[self.bzoffset:]
        self.writebit(0)
        self.writebyte(self.data[self.bzoffset])
        self.bzoffset += 1
        if debug: print "}"
        return

    def __windowblock(self, offset, length):
        if debug: print "blz: windowcopy {", offset, length
        self.writebit(1)
        self.writevariablenumber(length - 2)
        self.writevariablenumber(((offset >> 8) + 2) & 0xFF)
        self.writebyte((offset - 1) & 0xFF)
        self.bzoffset += length
        if debug: print "}"
        return

    def __determine(self, offset, length):
        """returns the correct encoding function based on the entry found"""
        if offset >= 1 or length >= 3:
            return self.__windowblock(offset, length)
        return self.__literal()

    def do(self):
        self.writebyte(self.data[self.bzoffset])
        self.bzoffset += 1
        while self.bzoffset < len(self.data):
            offset, length = misc.findlongeststring(self.data[:self.bzoffset],
                self.data[self.bzoffset:])
            self.__determine(offset, length)
        return self.getdata()


class decompress(lz.decompress):
    def __init__(self, data, length):
        self.data = lz.decompress.__init__(self, data, 2)
        self.decompressed = ""

        # brieflz specific
        self.length = length
        self.functions = [
            self.__literal,
            self.__windowblock
            ]

        self.functionsbits = len(self.functions) - 1
        return

    def do(self):
        """returns decompressed buffer and consumed bytes counter"""
        self.decompressed += self.readbyte()
        while self.offset < self.length:
            if self.functions[self.countbits(self.functionsbits)]():
                print "error"
                break

        return self.decompressed, self.offset

    def __literal(self):
        """copy literally the next byte from the bitstream"""
        self.decompressed += self.readbyte()
        return False

    def __windowblock(self):
        length = self.readvariablenumber() + 2
        offset = self.readvariablenumber() - 2
        offset = (offset << 8) + ord(self.readbyte()) + 1
        if debug:print "block read",offset, length
        try:
            self.windowblockcopy(offset, length)
        except:
            print "error windowblock"
            return True
        return False


if __name__ == '__main__':
    import test
    #test.brieflz_decompress()
    #test.brieflz_compdec(100,5)
    #s = "nO_NWS0>l>nnn2"
    original = "nn"
    c = compress(original)
    compressed = c.do()
    print original
    d = decompress(compressed, len(compressed))
    decompressed, consumed = d.do()
    print original, decompressed