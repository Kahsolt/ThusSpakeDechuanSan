#!/usr/bin/env python3
# Author: Armit
# Create Time: 2020/02/16 

# convert QQ chatlog files to clean sentence

import os
from os import path
import sys
import re

TITLE_REGEX = re.compile(r'(\d*-\d*-\d* \d*:\d*:\d*) (.*)')
AT_REGEX = re.compile(r'@[^ ]* ')
PUNC_REGEX = re.compile(r'！|？|。|（|）|“|”|\?|\(|\)')
SYM_REGEX = re.compile(r'\[图片\]|\[表情\]|/扯一扯|/佛系|/抱抱')

def open(fp:str, rw='r', **kwargs):
  from builtins import open as _open
  return 'b' in rw and _open(fp, rw, **kwargs) or _open(fp, rw, encoding='utf8', **kwargs)

def merge_corpus(dp):
  sents = [ ]
  for fn in os.listdir(dp):
    fp = path.join(dp, fn)
    with open(fp) as fh:
      for _ in range(8): line = fh.readline()
      lines = fh.read().split('\n')

      j = 0
      while j < len(lines):
        i = j ; j += 1
        while j < len(lines) and not TITLE_REGEX.findall(lines[j]):
          j += 1
        
        # now line[i] is cur title, line[j] is next title
        # now line[i+1:j-1] is content

        m = TITLE_REGEX.findall(lines[i])
        ts, sender = m[0]
        if '253803566' in sender or ('德川' in sender and '(' not in sender):
          for k in range(i+1, j):
            ln = lines[k]
            if ln == '[闪照]请使用新版手机QQ查看闪照': continue
            if ln.startswith('[自动回复]'): continue
            if ln.startswith('对方不想和你'): continue
            if ln.startswith('对方已拒收了您的消息'): continue
            ln = AT_REGEX.sub('', ln)
            ln = SYM_REGEX.sub('', ln)
            ln = PUNC_REGEX.sub('', ln)
            ln = ln.strip()
            if str.isdigit(ln): continue
            if len(ln) < 12: continue
            sents.append(ln)

  base_dp = path.dirname(path.abspath(dp))
  fn = path.basename(dp) + '.txt'
  fp = path.join(base_dp, fn)
  with open(fp, 'w') as fh:
    for sent in sorted(list(set(sents))):
      fh.write(sent)
      fh.write('\n')

  print("Corpus merged to %r" % fp)

if __name__ == "__main__":
  if len(sys.argv) < 2 or not path.exists(sys.argv[1]):
    print('Usage: %s <folder>' % sys.argv[0])
    exit(0)

  merge_corpus(sys.argv[1])
