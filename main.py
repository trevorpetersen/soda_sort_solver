import copy
import dataclasses
import itertools
import queue as queue_lib

class Bottle:
    name: str
    contents: list[str]

    def __init__(self, name: str, contents: list[str]):
        self.name = name
        self.contents = contents
        self._validate()

    def is_empty(self) -> bool:
        return not self.contents
    
    def is_full(self) -> bool:
        return len(self.contents) == 4

    def can_combine(self, bottle: 'Bottle') -> bool:
        if self.is_empty() or bottle.is_empty():
            return True
        
        if self.get_top_color() != bottle.get_top_color():
            return False
        
        if len(self.contents) + bottle.get_num_top_color() > 4:
            return False

        return True
    
    def combine(self, bottle: 'Bottle') -> None:
        if not self.can_combine(bottle):
            raise RuntimeError('Cannot combine')
        
        if bottle.is_empty():
            return
        
        color = bottle.get_top_color()
        self.contents += [color] * bottle.get_num_top_color()
        bottle.contents = bottle.contents[:-bottle.get_num_top_color()]        

    def get_num_top_color(self) -> int:
        if self.is_empty():
            return 0
        
        num = 1
        for i in range(len(self.contents) - 1):
            if self.get_top_color() == self.contents[-(i + 2)]:
                num += 1
            else:
                break

        return num

    def get_top_color(self) -> str:
        return self.contents[-1] if self.contents else None
    
    def is_single_color(self) -> bool:
        return self.get_num_top_color() == len(self.contents)

    def _validate(self):
        if (len(self.contents)) > 4:
            raise RuntimeError('Contents is too large')
    
    def __str__(self) -> str:
        return f'<{",".join(self.contents)}>'


class State:
    bottles: dict[str, Bottle]

    def __init__(self, bottles: list[Bottle]) -> None:
        self.bottles: dict[str, list[Bottle]] = {}

        for bottle in bottles:
            self.add_bottle(bottle)

    def find_bottle(self, bottle_to_find: Bottle, skip_first: bool) -> Bottle:
        count = 0
        target_count = 1 if skip_first else 0
        for bottle_list in self.bottles.values():
            for bottle in bottle_list:
                if str(bottle) == str(bottle_to_find):
                    if count == target_count:
                        return bottle
                    else:
                        count += 1

        raise RuntimeError(f'Cannot find {bottle_to_find} in {self}')

    def add_bottle(self, bottle: Bottle) -> None:
        key = 'empty' if bottle.is_empty() else bottle.get_top_color()
        if key not in self.bottles:
            self.bottles[key] = []

        self.bottles[key].append(bottle)

    def remove_bottle(self, bottle_to_remove: Bottle) -> None:
        for key in self.bottles.keys():
            bottle_list = self.bottles[key]

            for bottle in bottle_list:
                if str(bottle) == str(bottle_to_remove):
                    bottle_list.remove(bottle)
                    if not bottle_list:
                        self.bottles.pop(key)
                    return

        return None

    def copy(self) -> 'State':
        return copy.deepcopy(self)
    
    def from_combination(self, bottle_1: Bottle, bottle_2: Bottle) -> 'State':
        new_state = self.copy()

        bottle_1_in_new_state = new_state.find_bottle(bottle_1, skip_first=False)
        bottle_2_in_new_state = new_state.find_bottle(bottle_2, skip_first=str(bottle_1) == str(bottle_2))

        new_state.remove_bottle(bottle_1_in_new_state)
        new_state.remove_bottle(bottle_2_in_new_state)

        bottle_1_in_new_state.combine(bottle_2_in_new_state)

        new_state.add_bottle(bottle_1_in_new_state)
        new_state.add_bottle(bottle_2_in_new_state)

        return new_state
    
    def is_terminal(self) -> bool:
        if 'empty' in self.bottles and len(self.bottles.keys()) > 1:
            return False

        for bottle_list in self.bottles.values():
            for i in range(len(bottle_list)):
                bottle_1 = bottle_list[i]
                for j in range(i + 1, len(bottle_list)):
                    bottle_2 = bottle_list[j]
                    if bottle_1.can_combine(bottle_2):
                        return False
        
        return True
    
    def is_winning_state(self) -> bool:
        for bottle_list in self.bottles.values():
            for bottle in bottle_list:
                if not bottle.is_empty() and (not bottle.is_single_color() or not bottle.is_full()):
                    return False
                
        return True

    def __str__(self) -> str:
        hash_dict = {}
        keys = sorted(self.bottles.keys())
        for key in keys:
            hash_dict[key] = str(','.join(map(lambda bottle: str(bottle) , sorted(self.bottles[key], key=lambda bottle: str(bottle)))))

        return str(hash_dict)

@dataclasses.dataclass(frozen=True)
class StateTransition:
    original_state: State | None
    new_state: State
    bottle_1: Bottle | None
    bottle_2: Bottle | None

    def __eq__(self, __value: object) -> bool:
        return True

def get_all_next_states(state: State) -> list[tuple[Bottle, Bottle, State]]:
    seen_states = set([str(state)])
    next_states = []
    
    for key in state.bottles:
        pour_pairs = itertools.permutations(state.bottles[key], 2)
        for pair in pour_pairs:
            if pair[0].can_combine(pair[1]):
                new_state = state.from_combination(pair[0], pair[1])
                if str(new_state) not in seen_states:
                    seen_states.add(str(new_state))
                    next_states.append((pair[0], pair[1] ,new_state))

        if 'empty' in state.bottles:
            for bottle in state.bottles[key]:
                if bottle.is_empty():
                    continue
                
                empty_bottle = state.find_bottle(Bottle('', []), skip_first=False)
                new_state = state.from_combination(empty_bottle, bottle)
                if str(new_state) not in seen_states:
                    seen_states.add(str(new_state))
                    next_states.append((empty_bottle, bottle, new_state))

    return next_states

def get_winning_transition_chain(initial_state: State) -> list[StateTransition]:
    seen_states = set()
    queue = queue_lib.PriorityQueue()
    queue.put((0, [StateTransition(None, initial_state, None, None)]))

    while not queue.empty():
        data = queue.get()
        num_transitions: int = data[0]
        transitions: list[StateTransition] = data[1]
        print('Looking at', num_transitions, transitions[-1].new_state)

        current = transitions[-1]
        current_state_hash = str(current.new_state)
        if current_state_hash in seen_states:
            continue
        else:
            seen_states.add(current_state_hash)

        if current.new_state.is_winning_state():
            return transitions

        next_states = get_all_next_states(current.new_state)
        print('num next states', len(next_states))
        for bottle_1, bottle_2, next_state in next_states:
            item = (num_transitions + 1, transitions.copy() + [StateTransition(current.new_state.copy(), next_state, bottle_1, bottle_2)])
            queue.put(item)

    return []

def main():
    bottles =  [
        Bottle('R1 1', ['yel', 'tre', 'ora', 'blu']),
        Bottle('R1 2', ['cya', 'gre', 'pin', 'tre']),
        Bottle('R1 3', ['yel', 'pur', 'sky', 'red']),
        Bottle('R1 4', ['tre', 'sky', 'ora', 'pur']),
        Bottle('R1 5', ['cya', 'gra', 'pin', 'blu']),
        Bottle('R1 6', ['tre', 'yel', 'bro', 'cya']),
        Bottle('R1 7', ['bro', 'sky', 'pin', 'red']),

        Bottle('R2 1', ['ora', 'blu', 'cya', 'gra']),
        Bottle('R2 2', ['yel', 'gra', 'gre', 'gre']),
        Bottle('R2 3', ['sky', 'gre', 'pin', 'bro']),
        Bottle('R2 4', ['bro', 'pur', 'red', 'gra']),
        Bottle('R2 5', ['red', 'blu', 'pur', 'ora']),
        Bottle('R2 6', []),
        Bottle('R2 7', []),
    ]

    state = State(bottles)
    transitions = get_winning_transition_chain(state)

    print('Winning transitions:')
    for transition in transitions:
        print(f'\t{transition.bottle_2.name if transition.bottle_2 else "None"} -> {transition.bottle_1.name if transition.bottle_1 else "None"}')

main()