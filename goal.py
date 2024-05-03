"""CSC148 Assignment 2

CSC148 Winter 2024
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
Jaisie Sin, and Joonho Kim

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, Jaisie Sin, and Joonho Kim

Module Description:

This file contains the hierarchy of Goal classes and related helper functions.
"""
from __future__ import annotations
import random
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> list[Goal]:
    """Return a randomly generated list of goals with length <num_goals>.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Preconditions:
    - num_goals <= len(COLOUR_LIST)
    """
    goals = random.sample(COLOUR_LIST, num_goals)
    goal_type = random.choice([PerimeterGoal, BlobGoal])
    return [goal_type(goal) for goal in goals]


def flatten(block: Block) -> list[list[tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j].

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """

    grid_size = 2 ** block.max_depth
    block_unit_size = block.size // grid_size
    colour_grid = [[(0, 0, 0) for _ in range(grid_size)]
                   for _ in range(grid_size)]

    def fulfill_colour(current_block: Block) -> None:
        if not current_block.children:
            start_point = current_block.position[1] // block_unit_size,  \
                current_block.position[0] // block_unit_size
            fill_length = 2 ** (block.max_depth - current_block.level)
            for i in range(start_point[0], start_point[0] + fill_length):
                for j in range(start_point[1], start_point[1] + fill_length):
                    colour_grid[j][i] = current_block.colour
            return
        for child in current_block.children:
            fulfill_colour(child)

    fulfill_colour(block)
    return colour_grid


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - colour: The target colour for this goal, that is the colour to which
              this goal applies.
    """
    colour: tuple[int, int, int]

    def __init__(self, target_colour: tuple[int, int, int]) -> None:
        """Initialize this goal to have the given <target_colour>.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given <board>.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A goal to maximize the presence of this goal's target colour
    on the board's perimeter.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a PerimeterGoal is defined to be the number of unit cells
        on the perimeter whose colour is this goal's target colour. Corner cells
        count twice toward the score.
        """
        colour_to_count = self.colour
        perimeter_count = 0
        flat_board = flatten(board)
        colour_map = {
            (1, 128, 181): "Blue",
            (138, 151, 71): "Green",
            (199, 44, 58): "Red",
            (255, 211, 92): "Yellow"
        }
        colour_names = [["" for _ in range(len(flat_board))]
                        for _ in range(len(flat_board))]
        for i in range(len(flat_board)):
            for j in range(len(flat_board)):
                colour_names[i][j] = colour_map[flat_board[i][j]]

        board_size = len(flat_board)
        for i in range(board_size):
            if flat_board[i][0] == colour_to_count:
                perimeter_count += 1
            if flat_board[i][board_size - 1] == colour_to_count:
                perimeter_count += 1
            if flat_board[0][i] == colour_to_count:
                perimeter_count += 1
            if flat_board[board_size - 1][i] == colour_to_count:
                perimeter_count += 1
        return perimeter_count

    def description(self) -> str:
        """Return a description of this goal.
        """
        return "Perimeter Goal, Target colour is " + \
            colour_name(self.colour) + "."


class BlobGoal(Goal):
    """A goal to create the largest connected blob of this goal's target
    colour, anywhere within the Block.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a BlobGoal is defined to be the total number of
        unit cells in the largest connected blob within this Block.
        """
        result = 0
        flattened_board = flatten(board)
        n = len(flattened_board)
        visited = [[-1 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if visited[i][j] == -1 and flattened_board[i][j] == self.colour:
                    result = max(result, self._undiscovered_blob_size(
                        (i, j), flattened_board, visited))
        return result

    def _undiscovered_blob_size(self, pos: tuple[int, int],
                                board: list[list[tuple[int, int, int]]],
                                visited: list[list[int]]) -> int:
        """Return the size of the largest connected blob in <board> that (a) is 
        of this Goal's target <colour>, (b) includes the cell at <pos>, and (c)
        involves only cells that are not in <visited>.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure (to <board>) that, in each cell,
        contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.

        If <pos> is out of bounds for <board>, return 0.
        """
        def get_neighbour(i: int, j: int) -> list[(int, int)]:
            ns = [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
            return [n for n in ns if 0 <= n[0] < len(board)
                    and 0 <= n[1] < len(board)]
        i, j = pos
        if visited[i][j] != -1:
            return 0
        visited[i][j] = 0
        if board[i][j] != self.colour:
            return 0
        visited[i][j] = 1
        result = 1
        for neighbour in get_neighbour(i, j):
            result += self._undiscovered_blob_size(neighbour, board, visited)
        return result

    def description(self) -> str:
        """Return a description of this goal.
        """
        return "Blob Goal, Target colour is " + colour_name(self.colour) + "."


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
