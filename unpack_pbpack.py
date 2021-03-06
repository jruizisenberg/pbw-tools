#!/usr/bin/env python

from zipfile import ZipFile
from glob import glob
import sys, logging, os.path, os, struct, json

class BMPResource:
    def __init__(self, data):
        (self.scanlines,self.unknown_1,self.unknown_2,self.width,self.height) = struct.unpack("<hhlhh", data[:12])
        assert(self.unknown_1 == 4096)
        #assert(self.unknown_2 == 0)
        self.data = data[12:]
    
    def __repr__(self):
        return "<BMP %dx%d (%d scanlines) size %d>" % (self.width,self.height,self.scanlines,len(self.data))

class Resource:
    def __init__(self, raw, file):
        (self.index, self.offset, self.size, self.crc) = struct.unpack("<LLLL", raw)
        #Resources are loaded sequentially, so...
        self.raw_data = file.read(self.size)
        self.png = BMPResource(self.raw_data)
    
    def __str__(self):
        return self.raw_data
    
    def __repr__(self):
        return "<Resource %d @ %08x:%08x CRC:%08x %s>" % (self.index, self.offset, self.offset+self.size, self.crc, repr(self.png))

class PBPack:
    def __init__(self, pack):
        (self.resource_count, self.unknown_1, self.timestamp, self.name) = struct.unpack("<LLL16s", pack.read(12+16))
        resource_block = pack.read(4096)
        offset = 0
        self.resources = []
        for i in xrange(self.resource_count):
            offset = 16*i
            self.resources.append(Resource(resource_block[offset:offset+16], pack))
        before = pack.tell()
        remainder = pack.read()
        after = pack.tell()
        if before != after:
            log.error("Resource table stopped at offset %08X but %d bytes remain - writing to remainder.resource" % before, after)
            with open("remainder.resource", 'wb') as f:
                f.write(remainder)
    
    def __repr__(self):
        return "<PBPack %08X \"%s\" [%d]>" % (self.unknown_1, self.name, self.resource_count)

if __name__=="__main__":
    log = logging.getLogger()
    logging.basicConfig(format='%(message)s')
    log.setLevel(logging.DEBUG)
    
    log.info('Processing "%s"' % "app_resources.pbpack")
    p = PBPack(open("app_resources.pbpack"))
    log.info(p)
    
    if os.path.exists("manifest.json"):
        manifest = json.load(open("manifest.json", "r"))
        count = 0
        for resource in manifest['debug']['resourceMap']['media']:
            fn = "%s.%s" % (resource['defName'],resource['type'])
            log.info("Generating %s" % fn)
            with open(fn, 'wb') as f:
                f.write(str(p.resources[count]))
                log.info(repr(p.resources[count]))
                count += 1
        while count < p.resource_count:
            fn = "UNKNOWN-%d.resource" % count
            log.info("Generating %s" % fn)
            with open(fn, 'wb') as f:
                f.write(str(p.resources[count]))
                log.info(repr(p.resources[count]))
                count += 1