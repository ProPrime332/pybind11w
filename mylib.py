from dataclasses import dataclass
from typing import List, Callable

@dataclass
class CacheBlock:
    tag: int = 0
    valid: bool = False
    dirty: bool = False
    access_count: int = 0
    last_used_time: int = 0

    @property
    def lastUsedTime(self):
        return self.last_used_time

    @lastUsedTime.setter
    def lastUsedTime(self, value):
        self.last_used_time = value

class CacheSet:
    def __init__(self, associativity: int):
        self.blocks: List[CacheBlock] = [CacheBlock() for _ in range(associativity)]

class Cache:
    def __init__(self, num_sets: int, associativity: int, block_size: int):
        self.num_sets = num_sets
        self.associativity = associativity
        self.block_size = block_size
        self.sets = [CacheSet(associativity) for _ in range(num_sets)]

    def read(self, address: int, time: int, callback: Callable[[str], None]) -> bool:
        index = get_index(address, self.block_size, self.num_sets)
        tag = get_tag(address, self.block_size, self.num_sets)

        for block in self.sets[index].blocks:
            if block.valid and block.tag == tag:
                callback(f"HIT ✅ in Cache at index {index}\n")
                block.last_used_time = time
                block.access_count += 1
                return True

        self.replace_lru(index, tag, time)
        callback(f"MISS ❌ in Cache at index {index}\n")
        return False

    def write(self, address: int, time: int, callback: Callable[[str], None]) -> bool:
        index = get_index(address, self.block_size, self.num_sets)
        tag = get_tag(address, self.block_size, self.num_sets)

        for block in self.sets[index].blocks:
            if block.valid and block.tag == tag:
                callback(f"HIT ✅ Writing to Cache at index {index}\n")
                block.last_used_time = time
                block.access_count += 1
                block.dirty = True
                return True

        self.replace_lru(index, tag, time)
        callback(f"MISS ❌ Writing to Cache at index {index}\n")
        return False

    def replace_fifo(self, index: int, tag: int):
        for block in self.sets[index].blocks:
            if not block.valid:
                block.tag = tag
                block.valid = True
                return
        self.sets[index].blocks.pop(0)
        self.sets[index].blocks.append(CacheBlock(tag=tag, valid=True))

    def replace_lru(self, index: int, tag: int, time: int):
        for block in self.sets[index].blocks:
            if not block.valid:
                block.tag = tag
                block.valid = True
                block.last_used_time = time
                return

        lru_block = min(self.sets[index].blocks, key=lambda b: b.last_used_time)
        lru_block.tag = tag
        lru_block.valid = True
        lru_block.access_count = 0
        lru_block.last_used_time = time
        lru_block.dirty = False

    def replace_lfu(self, index: int, tag: int):
        lfu_block = min(self.sets[index].blocks, key=lambda b: b.access_count)
        lfu_block.tag = tag
        lfu_block.valid = True
        lfu_block.access_count = 1
        lfu_block.last_used_time = 0
        lfu_block.dirty = False

class MultiLevelCache:
    def __init__(self):
        self.total_hits = 0
        self.total_misses = 0
        self.L1 = Cache(2, 1, 64)
        self.L2 = Cache(4, 2, 64)
        self.L3 = Cache(8, 4, 64)

    def access_memory(self, address: int, time: int, callback: Callable[[str], None]) -> bool:
        def wrap(level):
            def inner(msg):
                if "HIT" in msg:
                    self.total_hits += 1
                elif "MISS" in msg:
                    self.total_misses += 1
                callback(f"{level} Cache: {msg}")
            return inner

        if self.L1.read(address, time, wrap("L1")):
            return True
        if self.L2.read(address, time, wrap("L2")):
            return True
        return self.L3.read(address, time, wrap("L3"))

    def write_memory(self, address: int, time: int, callback: Callable[[str], None]) -> bool:
        if self.L1.write(address, time, callback):
            return True
        if self.L2.write(address, time, callback):
            return True
        return self.L3.write(address, time, callback)

    def get_total_hits(self) -> int:
        return self.total_hits

    def get_total_misses(self) -> int:
        return self.total_misses

    # --- Aliases for GUI compatibility (camelCase methods) ---
    def accessMemory(self, address: int, time: int, callback: Callable[[str], None]) -> bool:
        return self.access_memory(address, time, callback)

    def writeMemory(self, address: int, time: int, callback: Callable[[str], None]) -> bool:
        return self.write_memory(address, time, callback)

    def getTotalHits(self) -> int:
        return self.get_total_hits()

    def getTotalMisses(self) -> int:
        return self.get_total_misses()

# --- Utility functions ---

def get_index(address: int, block_size: int, num_sets: int) -> int:
    return (address // block_size) % num_sets

def get_tag(address: int, block_size: int, num_sets: int) -> int:
    return address // (block_size * num_sets)

# Aliases for GUI compatibility
def getIndex(address: int, block_size: int, num_sets: int) -> int:
    return get_index(address, block_size, num_sets)

def getTag(address: int, block_size: int, num_sets: int) -> int:
    return get_tag(address, block_size, num_sets)
