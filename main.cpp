#include <pybind11/stl.h>
#include <iostream>
#include <vector>
#include <functional>

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

    bool read(int address, int time, std::function<void(std::string)> callback);
    bool write(int address, int time, std::function<void(std::string)> callback);
    void replaceFIFO(int index, int tag);
    void replaceLRU(int index, int tag, int time);
    void replaceLFU(int index, int tag);
};

class MultiLevelCache {
    public:
        int total_hits = 0;  // Track total cache hits
        int total_misses = 0; // Track total cache misses
        Cache L1, L2, L3;
    
        MultiLevelCache()
            : L1(4, 2, 64),
              L2(8, 4, 64),
              L3(16, 4, 64) {}
    
        bool accessMemory(int address, int time, std::function<void(std::string)> callback);
        bool write_memory(int address, int time, std::function<void(std::string)> callback) {
            bool hit = L1.write(address, time, callback);
            if (!hit) hit = L2.write(address, time, callback);
            if (!hit) hit = L3.write(address, time, callback);
            return hit;
    
        int getTotalHits() {
            return total_hits;  // Return total hits count
        }
    
        int getTotalMisses() {
            return total_misses;  // Return total misses count
        }
    };

int getIndex(int address, int blockSize, int numSets) {
    return (address / blockSize) % numSets;
}

int getTag(int address, int blockSize, int numSets) {
    return address / (blockSize * numSets);
}

bool Cache::read(int address, int time, std::function<void(std::string)> callback) {
    int index = getIndex(address, blockSize, numSets);
    int tag = getTag(address, blockSize, numSets);

    for (CacheBlock &block : sets[index].blocks) {
        if (block.valid && block.tag == tag) {
            std::string msg = "HIT ✅ in Cache at index " + std::to_string(index) + "\n";
            callback(msg);  // Pass message back to Python
            block.lastUsedTime = time;
            block.accessCount++;
            return true;
        }
    }

    replaceLRU(index, tag, time);
    std::string msg = "MISS ❌ in Cache at index " + std::to_string(index) + "\n";
    callback(msg);  // Pass message back to Python
    return false;
}

bool Cache::write(int address, int time, std::function<void(std::string)> callback) {
    int index = getIndex(address, blockSize, numSets);
    int tag = getTag(address, blockSize, numSets);

    for (CacheBlock &block : sets[index].blocks) {
        if (block.valid && block.tag == tag) {
            std::string msg = "HIT ✅ Writing to Cache at index " + std::to_string(index) + "\n";
            callback(msg);  // Pass message back to Python
            block.lastUsedTime = time;
            block.accessCount++;
            block.dirty = true;
            return true;
        }
    }

    replaceLRU(index, tag, time);
    std::string msg = "MISS ❌ Writing to Cache at index " + std::to_string(index) + "\n";
    callback(msg);  // Pass message back to Python
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

bool MultiLevelCache::accessMemory(int address, int time, std::function<void(std::string)> callback) {
    bool result = L1.read(address, time, [&](const std::string& msg) {
        if (msg.find("HIT") != std::string::npos) {
            total_hits++;  // Increment total hit count
        }
        if (msg.find("MISS") != std::string::npos) {
            total_misses++;  // Increment total miss count
        }
        callback("L1 Cache: " + msg);
    });
    if (result) return true;

    result = L2.read(address, time, [&](const std::string& msg) {
        if (msg.find("HIT") != std::string::npos) {
            total_hits++;  // Increment total hit count
        }
        if (msg.find("MISS") != std::string::npos) {
            total_misses++;  // Increment total miss count
        }
        callback("L2 Cache: " + msg);
    });
    if (result) return true;

    result = L3.read(address, time, [&](const std::string& msg) {
        if (msg.find("HIT") != std::string::npos) {
            total_hits++;  // Increment total hit count
        }
        if (msg.find("MISS") != std::string::npos) {
            total_misses++;  // Increment total miss count
        }
        callback("L3 Cache: " + msg);
    });
    return result;

}

// ⬇ pybind11 bindings
PYBIND11_MODULE(mylib, m) {
    py::class_<CacheBlock>(m, "CacheBlock")
        .def(py::init<>())
        .def(py::init<int, bool, bool, int, int>())
        .def_readwrite("tag", &CacheBlock::tag)
        .def_readwrite("valid", &CacheBlock::valid)
        .def_readwrite("dirty", &CacheBlock::dirty)
        .def_readwrite("accessCount", &CacheBlock::accessCount)
        .def_readwrite("lastUsedTime", &CacheBlock::lastUsedTime);

    py::class_<CacheSet>(m, "CacheSet")
        .def(py::init<int>())
        .def_readwrite("blocks", &CacheSet::blocks);

    py::class_<Cache>(m, "Cache")
        .def(py::init<int, int, int>())
        .def("read", &Cache::read)
        .def("write", &Cache::write)
        .def("replaceFIFO", &Cache::replaceFIFO)
        .def("replaceLRU", &Cache::replaceLRU)
        .def("replaceLFU", &Cache::replaceLFU)
        .def_readonly("blockSize", &Cache::blockSize)
        .def_readonly("numSets", &Cache::numSets)
        .def_readwrite("sets", &Cache::sets)
        .def_property_readonly("num_sets", [](const Cache &c) { return c.numSets; })
        .def_property_readonly("associativity", [](const Cache &c) { return c.associativity; })
        .def_property_readonly("block_size", [](const Cache &c) { return c.blockSize; });

    py::class_<MultiLevelCache>(m, "MultiLevelCache")
        .def(py::init<>())
        .def_readonly("L1", &MultiLevelCache::L1)
        .def_readonly("L2", &MultiLevelCache::L2)
        .def_readonly("L3", &MultiLevelCache::L3)    
        .def("accessMemory", &MultiLevelCache::accessMemory)
        .def("getTotalHits", &MultiLevelCache::getTotalHits)
        .def("getTotalMisses", &MultiLevelCache::getTotalMisses)
        .def("accessMemory", [](MultiLevelCache &self, int address, int time, py::function py_callback) { return self.accessMemory(address, time, [py_callback](const std::string& msg) { py_callback(msg); }); }, "Access memory with logging callback")
        .def("write_memory", [](MultiLevelCache &self, int address, int time, py::function py_callback) { return self.write_memory(address, time, [py_callback](const std::string& msg) { py_callback(msg); }); }, "write memory with logging callback");
        m.def("getIndex", &getIndex, "Calculate cache index from address", py::arg("address"), py::arg("block_size"), py::arg("num_sets"));
        m.def("getTag", &getTag, "Calculate cache tag from address", py::arg("address"), py::arg("block_size"), py::arg("num_sets"));
}
