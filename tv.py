# tv.py
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import pickle
import hashlib
import struct
import time
import sys
import zstandard as zstd
#from functools import lru_cache
from cachetools import LFUCache,LRUCache,cached
from typing import Any


_char = "▄"
pixel_cache = LFUCache(8192)
frame_cache = LRUCache(2048)
version = "v0.0.2"


def myprint(text:str):
    sys.stdout.write(text)
    sys.stdout.flush()


#@lru_cache(maxsize=pixel_cache_size)
@cached(pixel_cache)
def transform(ur:int,ug:int,ub:int,lr:int,lg:int,lb:int,char:str = _char) -> str:
    return "\033[38;2;{0};{1};{2};48;2;{3};{4};{5}m{6}".format(lr,lg,lb,ur,ug,ub,char)


def save(lst:tuple[tuple[tuple[int,int,int,int,int,int]]] | tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]] | Any,path:str,level:int = 3):
    byte = zstd.compress(pickle.dumps(lst,5),level)
    len_byte = struct.pack("<I",len(byte))
    hash_byte = hashlib.sha512(len_byte + byte).digest()
    try:
        with open(path,"wb") as f:
            f.write(len_byte + byte + hash_byte)
    except Exception as e:
        raise ValueError(f"Err:{e}")


def load(path:str) -> tuple[tuple[tuple[int,int,int,int,int,int]]] | tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]] | Any:
    try:
        with open(path,'rb') as f:
            head = f.read(4)
            if len(head) < 4:
                raise ValueError("File is empty or too small to be a valid file")
            len_byte = struct.unpack("<I",head)[0]
            byte = f.read(len_byte)
            if len(byte) < len_byte:
                raise ValueError("File is too small to be a valid file")
            if hashlib.sha512(head + byte).digest() == f.read():
                return pickle.loads(zstd.decompress(byte))
            else:
                raise Exception("Verification failed.")
    except Exception as e:
        raise e


#@lru_cache(maxsize=frame_cache_size)
@cached(frame_cache)
def parse(lst:tuple[tuple[tuple[int,int,int,int,int,int]]],char:str = _char) -> str:
    code = ''
    try:
        for i in lst:
            for l in i:
                code += transform(*l,char)
            code += "\033[0m\n"
        return code.removesuffix("\n")
    except Exception as e:
        raise ValueError(f"Invalid data, Err:{e}")

def parse_frames(lst:tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]],char:str = _char) -> tuple[str]:
    codes = []
    try:
        for i in lst:
            codes.append(parse(i,char))
        return tuple(codes)
    except Exception as e:
        raise e

def play_video(lst:tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]],char:str = _char,fps:int = 30):
    s_time = 1 / fps
    try:
        myprint('\033[?1049h\033[?25l')
        for i in lst:
            myprint(parse(i,char))
            time.sleep(s_time)
            myprint("\033[H")
        myprint('\033[?1049l\033[?25h')
    except KeyboardInterrupt:
        return
    except Exception as e:
        raise e
    finally:
        myprint('\033[?1049l\033[?25h')

def play_parsed_video(lst:tuple[str],char:str = _char,fps:int = 30):
    s_time = 1 / fps
    try:
        myprint('\033[?1049h\033[?25l')
        for i in lst:
            myprint(i)
            time.sleep(s_time)
            myprint("\033[H")
        myprint('\033[?1049l\033[?25h')
    except KeyboardInterrupt:
        return
    except Exception as e:
        raise e
    finally:
        myprint('\033[?1049l\033[?25h')

def show_photo(lst:tuple[tuple[tuple[int,int,int,int,int,int]]],char:str = _char):
    try:
        myprint(parse(lst,char))
    except Exception as e:
        raise e

def show_parsed_photo(data:str,char:str = _char):
    try:
        myprint(data)
    except Exception as e:
        raise e