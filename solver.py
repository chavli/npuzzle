from board import NPuzzleBoard, NPuzzleCoordinate
import pdb
import random 
import operator
import time
import numpy as np

N = 5

# ---------- 5x5 andreas puzzles -------------------------------------------------------------------
# trials = 10, avg_t = 24.9s, max_t = 49s, min_t = 6s, avg_depth = 687
# start = [ 8,17,13, 4, 1,  2, 7,15,14,16, 22,11, 5,10, 0,  6,20, 3,23,24, 12, 9,19,21,18]

# 5x5 shuffle start
# start = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 0]

# trials = 10, avg_t = 26.4s, max_t = 64s, min_t = 10s, avg_depth = 709
# start = [ 0, 7,12, 8, 4,  5,22,17,11,15,  1,10,18, 6,19,  2,20, 3, 9,24, 16,23,21,14,13]

# trials = 10, avg_t = 18.2s, max_t = 40s, min_t = 5s, avg_depth = 518.2
# start = [ 6, 0,17, 9,11,  8, 2,10,15, 4, 21, 1,20,13, 3, 16,23,18,14,12,  7,22,19,24, 5]

# trials = 10, avg_t = 27.1s, max_t = 69s, min_t = 7s, avg_depth = 816
# start = [18, 9,15, 7,23, 12, 6,10,16, 1, 22,11,24, 2,20, 13,14,19, 8, 3, 21, 4, 5, 0,17]

# 5x5 random start, created by andreas
start = [8 ,17 ,13 ,4 ,1 ,2 ,7 ,15 ,14 ,16 ,22 ,11 ,5 ,10, 0 ,6 ,20 ,3 ,23 ,24 ,12 ,9 ,19 ,21 ,18]
# start = [3, 11, 24, 6, 2, 9, 0, 14, 18, 5, 1, 8, 23, 16, 13, 21, 20, 10, 12, 7, 22, 4, 19, 17, 15]

# --------------------------------------------------------------------------------------------------
# board creation
# --------------------------------------------------------------------------------------------------
def shufflestart(n=10000):
    """ increasing shuffle count creates harder puzzles. """
    solution = []
    start = range(1, N**2) + [0]
    board = NPuzzleBoard(None, N, 0, start)
    for i in range(0, n):
        swaps = board.possibleswaps()
        val = swaps[random.randint(0, len(swaps)-1)]
        board = board.swap(val)
        solution.append(val)
    
    solution.reverse()

    return board, solution

def definestart(preconfig):
    board = NPuzzleBoard(None, N, 0, preconfig)
    return board

# --------------------------------------------------------------------------------------------------
# temperature func for SA, can be any function with a range of [0, 1]
# --------------------------------------------------------------------------------------------------
def temperature(x, annealing=1.0):
    """ returns a value [0, 1]. used by simulated annealing to determine if a worse path should be
        tried. rate determines 'leniency'. a large annealing  means SA will get to choose worse 
        options for a longer time """
    return 1.0 * x / (annealing + x)


# --------------------------------------------------------------------------------------------------
# temperature
# --------------------------------------------------------------------------------------------------
def temperature(x, annealing=100):
    """ the temperature function used by simulated annealing to decide if a local sub-optimal 
        state should be explored """
    return 1.0 * x / (annealing + x)

# --------------------------------------------------------------------------------------------------
# board heuristics
# --------------------------------------------------------------------------------------------------
def mdist_entropy(board):
    """ messiness of board defined as sum of some distance metric, manhattan in this case """
    total_entropy = 0
    
    # calculate the L1 distance of each piece [1, N^2). the final 1-D position of each piece is 
    # its value - 1
    for i in range(1, N**2):
        targetpos = NPuzzleCoordinate(N, i - 1)
        currentpos = board.positionof(i)

        total_entropy += targetpos.mdist(currentpos)

    return total_entropy

def avgmdist_entropy(board):
    """ messiness of board defined as average manhattan distance of misplaced pieces """
    total_mdist = 0
    total_misplaced = 0

    for i in range(1, N**2):
        targetpos = NPuzzleCoordinate(N, i - 1)
        currentpos = board.positionof(i)
        
        dist = targetpos.mdist(currentpos)
        total_mdist += dist
        if total_mdist > 0: total_misplaced += 1

    return 1.0 * total_mdist / total_misplaced


# --------------------------------------------------------------------------------------------------
# search algorithms
# --------------------------------------------------------------------------------------------------
def iddfs(startboard):
    """ iterative deepening DFS """ 
    
    def dfs(path, cur_depth, maxdepth):
        if path[-1].iscomplete():
            return path
        if cur_depth == maxdepth:
            return None
        
        working_board = path[-1]
        
        for possible in working_board.possibleswaps():
            nextboard = working_board.swap(possible)
            result = dfs(path + [nextboard], cur_depth + 1, maxdepth)
            if result:
                return result
        
        return None

    for limit in range(5, 200):
        result = dfs([startboard], 1, limit)
         
        if result:
            return result
    
    return None


# --------------------------------------------------------------------------------------------------
def beamlike(starting_board, hfunc=mdist_entropy):
    """ a search algorithm similar to beam search. it's something i made up """
    entropies = {} # map of board hash -> entropy cost
    explored = {} # map of board hash -> board object
    ticks = 0 # used for SA

    def dfs_lookahead(board, cur_depth, max_depth):
       
       # winning board found, return 0
       if board.iscomplete(): return 0

       # we've done a lookahead on this state already so return its precalculated entropy value
       if board.hash in explored: return hfunc(explored[board.hash])

       # we've reached max lookahead, calculate entropy and return
       if cur_depth == max_depth: return hfunc(board)
       
       min_cost = 999999999
       for possible in board.possibleswaps():
           nextboard = board.swap(possible)
           cost = dfs_lookahead(nextboard, cur_depth + 1, max_depth)
           min_cost = min(cost, min_cost)
       
       return min_cost
    

    # add the starting board
    fringe[ starting_board.hash ] = hfunc(starting_board)
    explored[ starting_board.hash ] = starting_board

    while len(fringe) > 0:
        
        # pick the board with that leads to the lowest entropy board
        sorted_boards = sorted(entropies.items(), key=operator.itemgetter(1))
        
        # thresh = temperature(ticks, annealing=10)
        # thresh = 1
        # if random.random() >= thresh:
        #     # pick a locally suboptimal choice and hope for a better outcome
        #     ix = random.randint(0, len(sorted_boards) - 1)
        # else:
        #     # pick optimal choice
        #     ix = 0
        
        parent_hash = sorted_boards[0][0]
        parent_board = explored[parent_hash]
        
        entropies.pop(parent_hash, None)
        
        # the next node to explore
        parent_hash = sorted_boards[ix][0]
        parent_board = explored[parent_hash]
        fringe.pop(parent_hash, None)

        if parent_board.iscomplete():
            print "WINNING !!!!!"
            break
        
        for possible in parent_board.possibleswaps():
            working_board = parent_board.swap(possible)
            cost = dfs_lookahead(working_board, 1, 6)
            
            if working_board.hash not in explored:
                thresh = temperature(ticks, annealing=10000)
                if random.random() >= thresh:
                    entropies[working_board.hash] = cost
                    explored[working_board.hash] = working_board
        
        ticks += 1

    # this is the solved board
    return parent_board, len(explored)

# --------------------------------------------------------------------------------------------------
# execution starts here
# --------------------------------------------------------------------------------------------------
def main():
    # create a random solvable board
    # board, solution = shufflestart(n=3) 
    
    # create a board from a given array of ints
    board = definestart(start)
    
    print "-" * 100
    print "====== START BOARD ======",
    print board
    print "-" * 100


    # result = iddfs(board)
    solved_board, n_explored = beamlike(board, hfunc=mdist_entropy)

    # we're iterating backwards, solution -> original. reorganize for pretty
    # printing
    solution = []
    while solved_board:
        solution.append(solved_board)
        solved_board = solved_board.parent
    
    times = []
    depths = []
    widths = []
    for trial in range(0, trials):
        print "starting trial %s" % trial

        board, solution = shufflestart() 
        # board = definestart(start)
        
        # set board to be root
        board.parent = None
        board.depth = 0
        
        s = int(time.time())
        # result = iddfs(board)
        solved_board, n_explored = sa_beam(board, hfunc=mdist_entropy)
        s = int(time.time()) - s

        times.append(s)

        # we're iterating backwards, solution -> original. reorganize for pretty
        # printing
        solution = []
        while solved_board:
            solution.append(solved_board)
            solved_board = solved_board.parent
        
        depths.append(len(solution))
        widths.append(n_explored)
     
        solution.reverse()
        for step in solution:
            print step
       
        print "results: time: %ss, depth: %s, width: %s" % (s, len(solution), n_explored)
    
    print "\n ----> results",
    print board
    print "avg_t: %s" % np.average(times)
    print "max_t: %s" % np.max(times)
    print "min_t: %s" % np.min(times)
    print "avg_depth: %s" % np.average(depths)

# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
