import mylib

cache = mylib.MultiLevelCache()

# Simulate a few memory accesses
print("Accessing address 0x1000 at time 1:")
cache.accessMemory(0x1000, 1)

print("\nAccessing address 0x2000 at time 2:")
cache.accessMemory(0x2000, 2)

print("\nAccessing address 0x1000 again at time 3:")
cache.accessMemory(0x1000, 3)

print("\nAccessing address 0x4000 at time 4:")
cache.accessMemory(0x4000, 4)

print("\nAccessing address 0x9000 at time 5:")
cache.accessMemory(0x9000, 5)
