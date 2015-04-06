"""
    board.py

    The n-puzzle board
"""
import copy

# --------------------------------------------------------------------------------------------------
class NPuzzleBoard:
    
    def __init__(self, parent, n, depth, preconfig = None):
        self.N = n
        self.boardvals = []
        self.parent = parent
        self.depth = depth

        if preconfig:
            for i in range(0, len(preconfig)):
                self.boardvals.append(preconfig[i])
        else:
            self.boardvals = [x for x in range(0, n**2)]
        
        # now that board is setup, we can hash it. an instance of a board is never updated in-place
        # so this hash will always be accurate
        self.hash = hash(tuple(self.boardvals))

    def __str__(self):
        s = ""
        for i in range(0, len(self.boardvals)): 
            if i % self.N == 0:
                s += "\n"
            # s += ("%3s" % self.board[i].val)
            s += ("%3s" % self.boardvals[i])
        
        s += "\niscomplete: %s" % self.iscomplete()
        return s
    
    def positionof(self, val):
        for i in range(0, len(self.boardvals)):
            if val == self.boardvals[i]:
                return NPuzzleCoordinate(self.N, i) 
        return None

    def iscomplete(self):
        # len -1 because we only check the position of the first 15 pieces
        for i in range(0, len(self.boardvals) - 1): 
            if i+1 != self.boardvals[i]: return False
        
        return True
    
    def possibleswaps(self):
        """ return the values that can be swapped """
        possible = []

        # 1-d index offsets from zero's position of possible swappable pieces
        idxoffsets = [-1, 1, -self.N, self.N]
        zeropos = self.positionof(0)
        for delta in idxoffsets:
            if zeropos.idx + delta >= 0 and zeropos.idx + delta < self.N**2:
                targetpos = NPuzzleCoordinate(self.N, zeropos.idx + delta)
                if zeropos.mdist(targetpos) == 1:
                    possible.append(self.boardvals[zeropos.idx + delta])

        return possible

    def swap(self, val):
        zeropos = self.positionof(0)
        valpos = self.positionof(val)
        
        if valpos.mdist(zeropos) == 1:
            zeroidx = zeropos.idx
            validx = valpos.idx
            
            # do the piece swap
            newconfig = copy.deepcopy(self.boardvals)
            temp = newconfig[zeroidx]
            newconfig[zeroidx] = newconfig[validx]
            newconfig[validx] = temp

            newboard = NPuzzleBoard(self, self.N, self.depth + 1, newconfig)
            return newboard
        else:
            return None

# --------------------------------------------------------------------------------------------------
class NPuzzleCoordinate:
    def __init__(self, n, ix):
        self.row = ix / n
        self.col = ix % n
        self.n = n
        self.idx = ix
    
    def __str__(self):
        return  "(%s, %s)" % (self.row, self.col)
    
    def mdist(self, other):
        """ manhattan dist between this position and other position """
        cdist = abs(self.col - other.col) 
        rdist = abs(self.row - other.row)
        return cdist + rdist

