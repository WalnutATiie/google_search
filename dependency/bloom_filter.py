'''
Module of bloom filter from Github.com(https://github.com/EverythingMe/inbloom)
Thank you Boy this is a very tricky implementation:)

class of bloom filter.
class:
    @bloom_capacity:Capacity of the buffer
    @error_rate:rate of error capacity
    @bf:init
    func bf_add(str):add a item into the buffer
    func is_not_contained(str):if str is not in the buffer, return 1 else return 0
'''
import inbloom
class BloomFilter:
    def __init__(self,bloom_capacity,error_rate):
        self.bloom_capacity = bloom_capacity
        self.error_rate = error_rate
        self.bf = inbloom.Filter(entries=bloom_capacity, error=error_rate)
    def bf_add(self,str):
        self.bf.add(str)
    def is_not_contained(self,str):
        if self.bf.contains(str):
            return 0
        else:
            return 1