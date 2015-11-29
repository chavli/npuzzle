from board import NPuzzleBoard, NPuzzleCoordinate
import pdb
import random 
import operator

N = 5

# 4x4 shuffle start
# start = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0] 

# 5x5 shuffle start
# start = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 0]

# 4x4 random solvable defined start
# start = [5, 3, 4, 15, 12, 13, 2, 0, 7, 6, 10, 9, 11, 8, 14, 1]

# 5x5 random solvable defined start
# start = [15, 3, 6, 23, 24, 12, 10, 7, 20, 14, 16, 19, 11, 9, 5, 8, 18, 22, 17, 4, 0, 21, 2, 13, 1]

# 4x4 toy defined start, two swaps from solution
# start =  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0, 11, 13, 14, 15, 12]

# 5x5 random start, created by andreas
start = [8 ,17 ,13 ,4 ,1 ,2 ,7 ,15 ,14 ,16 ,22 ,11 ,5 ,10, 0 ,6 ,20 ,3 ,23 ,24 ,12 ,9 ,19 ,21 ,18]
# start = [3, 11, 24, 6, 2, 9, 0, 14, 18, 5, 1, 8, 23, 16, 13, 21, 20, 10, 12, 7, 22, 4, 19, 17, 15]

# --------------------------------------------------------------------------------------------------
# board creation
# --------------------------------------------------------------------------------------------------
def shufflestart(n=50000):
    """ increasing shuffle count creates harder puzzles. i can't handle 10,000 or more shuffles """
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
    entropies[ starting_board.hash ] = hfunc(starting_board)
    explored[ starting_board.hash ] = starting_board

    while len(entropies) > 0:
        
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
    
    solution.reverse()
    
    for step in solution:
        print step
    print "solved in %s moves, %s nodes explored" % (len(solution), n_explored)



# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
