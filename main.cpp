#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <iostream>
#include <vector>

namespace py = pybind11;
using namespace std;

struct CacheBlock {
    int tag;
    bool valid;
    bool dirty;
    int accessCount;
    int lastUsedTime;

    CacheBlock() : tag(0), valid(false), dirty(false), accessCount(0), lastUsedTime(0) {}
    CacheBlock(int t, bool v, bool d, int ac, int lut) : tag(t), valid(v), dirty(d), accessCount(ac), lastUsedTime(lut) {}
};

struct CacheSet {
    vector<CacheBlock> blocks;
    CacheSet(int associativity) {
        blocks.resize(associativity);
    }
};

class Cache {
public:
    int numSets;
    int associativity;
    int blockSize;
    vector<CacheSet> sets;

    Cache(int numSets, int associativity, int blockSize)
        : numSets(numSets), associativity(associativity), blockSize(blockSize) {
        sets.resize(numSets, CacheSet(associativity));
    }

    bool read(int address, int time);
    bool write(int address, int time);
    void replaceFIFO(int index, int tag);
    void replaceLRU(int index, int tag, int time);
    void replaceLFU(int index, int tag);
};

class MultiLevelCache {
public:
    Cache L1, L2, L3;

    MultiLevelCache()
        : L1(64, 4, 64),
          L2(256, 8, 64),
          L3(1024, 16, 64) {}

    bool accessMemory(int address, int time);
};

int getIndex(int address, int blockSize, int numSets) {
    return (address / blockSize) % numSets;
}

int getTag(int address, int blockSize, int numSets) {
    return address / (blockSize * numSets);
}

bool Cache::read(int address, int time) {
    int index = getIndex(address, blockSize, numSets);
    int tag = getTag(address, blockSize, numSets);

    for (CacheBlock &block : sets[index].blocks) {
        if (block.valid && block.tag == tag) {
            cout << "HIT ✅ in Cache at index " << index << "\n";
            block.lastUsedTime = time;
            block.accessCount++;
            return true;
        }
    }

    replaceLRU(index, tag, time);
    return false;
}

bool Cache::write(int address, int time) {
    int index = getIndex(address, blockSize, numSets);
    int tag = getTag(address, blockSize, numSets);

    for (CacheBlock &block : sets[index].blocks) {
        if (block.valid && block.tag == tag) {
            cout << "HIT ✅ Writing to Cache at index " << index << "\n";
            block.lastUsedTime = time;
            block.accessCount++;
            block.dirty = true;
            return true;
        }
    }

    replaceLRU(index, tag, time);
    return false;
}

void Cache::replaceFIFO(int index, int tag) {
    for (CacheBlock &block : sets[index].blocks) {
        if (!block.valid) {
            block = CacheBlock(tag, true, false, 0, 0);
            return;
        }
    }
    sets[index].blocks.erase(sets[index].blocks.begin());
    sets[index].blocks.push_back(CacheBlock(tag, true, false, 0, 0));
}

void Cache::replaceLRU(int index, int tag, int time) {
    for (CacheBlock &block : sets[index].blocks) {
        if (!block.valid) {
            block = CacheBlock(tag, true, false, 0, time);
            return;
        }
    }

    int lruIndex = 0, oldestTime = sets[index].blocks[0].lastUsedTime;
    for (int i = 1; i < associativity; i++) {
        if (sets[index].blocks[i].lastUsedTime < oldestTime) {
            lruIndex = i;
            oldestTime = sets[index].blocks[i].lastUsedTime;
        }
    }

    sets[index].blocks[lruIndex] = CacheBlock(tag, true, false, 0, time);
}

void Cache::replaceLFU(int index, int tag) {
    int lfuIndex = 0;
    int leastUsed = sets[index].blocks[0].accessCount;

    for (int i = 1; i < associativity; i++) {
        if (sets[index].blocks[i].accessCount < leastUsed) {
            lfuIndex = i;
            leastUsed = sets[index].blocks[i].accessCount;
        }
    }

    sets[index].blocks[lfuIndex] = CacheBlock(tag, true, false, 1, 0);
}

bool MultiLevelCache::accessMemory(int address, int time) {
    if (L1.read(address, time)) return true;
    if (L2.read(address, time)) {
        cout << "Moving block from L2 → L1\n";
        L1.replaceLRU(getIndex(address, L1.blockSize, L1.numSets), getTag(address, L1.blockSize, L1.numSets), time);
        return true;
    }
    if (L3.read(address, time)) {
        cout << "Moving block from L3 → L2 → L1\n";
        L2.replaceLRU(getIndex(address, L2.blockSize, L2.numSets), getTag(address, L2.blockSize, L2.numSets), time);
        L1.replaceLRU(getIndex(address, L1.blockSize, L1.numSets), getTag(address, L1.blockSize, L1.numSets), time);
        return true;
    }

    cout << "MISS ❌ Loading from RAM to L3 → L2 → L1\n";
    L3.replaceLRU(getIndex(address, L3.blockSize, L3.numSets), getTag(address, L3.blockSize, L3.numSets), time);
    L2.replaceLRU(getIndex(address, L2.blockSize, L2.numSets), getTag(address, L2.blockSize, L2.numSets), time);
    L1.replaceLRU(getIndex(address, L1.blockSize, L1.numSets), getTag(address, L1.blockSize, L1.numSets), time);

    return false;
}

// ⬇ pybind11 bindings
PYBIND11_MODULE(mylib, m) {
    py::class_<MultiLevelCache>(m, "MultiLevelCache")
        .def(py::init<>())
        .def("accessMemory", &MultiLevelCache::accessMemory, "Access memory at address and time");
}
