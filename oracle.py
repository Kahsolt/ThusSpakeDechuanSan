#!/usr/bin/env python3w
# Author: Armit
# Create Time: 2020/02/16 
# Update Time: 2020/02/26 

import os
from os import path
import sys
import re
import json
import pickle
import jieba
import random
from collections import Counter, defaultdict
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import tkinter.messagebox as tkmsg
import tkinter.filedialog as tkfiledlg
import tkinter.scrolledtext as tkscrtxt

__version__ = '0.1'

# settings
BASE_PATH = path.dirname(path.abspath(__file__))
CONFIG_FILE = 'config.json'
CORPUS_DIR = 'corpus'
MODEL_DIR = 'models'
STOPWORDS_FILE = path.join(MODEL_DIR, 'stopwords_cn.txt')

WINDOW_TITLE = "Thus Spake Dechuan-san (Ver %s)" % __version__
WINDOW_SIZE = (400, 500)
ALGORITHM_TYPE = '2-gram'   # ['2-gram', '3-gram']

# sysfix
def open(fp:str, rw='r', **kwargs):
  from builtins import open as _open
  return 'b' in rw and _open(fp, rw, **kwargs) or _open(fp, rw, encoding='utf8', **kwargs)

def read_file(fp:str) -> str:
  def fuck_encoding(bdata:bytes) -> str:
    for encoding in ['gb18030', 'ascii', 'utf8']:
      try: return bdata.decode(encoding)
      except UnicodeDecodeError: pass
    return None
  with open(fp, 'rb') as fp:
    return fuck_encoding(fp.read())

# app
class NGram:

  def __init__(self, fp:str=None):
    pkl = { }
    if fp and path.exists(fp):
      with open(fp, 'rb') as fh:
        pkl = pickle.load(fh)
    
    self.nsent  = pkl.get('nsent')
    self.ntoken = pkl.get('ntoken')
    self.nvocab = pkl.get('nvocab')
    self.tfreq  = pkl.get('tfreq')
    self.PI     = pkl.get('PI')
    self.T2     = pkl.get('T2')
    self.T3     = pkl.get('T3')

  @staticmethod
  def _ctor():
    return defaultdict(list)

  @classmethod
  def create_model(cls, fp:str):
    nsent = 0
    vocabs, tokens, PI = set(), list(), set()
    T2, T3 = defaultdict(list), defaultdict(NGram._ctor)

    with open(fp) as fh:
      for line in fh.readlines():
        nsent += 1
        toks = jieba.lcut(line)
        tokens.extend(toks)
        vocabs = vocabs.union(toks)
        if len(toks): PI.add(toks[0])     # init token

        for x, y in zip(toks, toks[1:]):  # transfer matrix
          if y not in T2[x]:
            T2[x].append(y)
        for x, y, z in zip(toks, toks[1:], toks[2:]):
          if z not in T3[x][y]:
            T3[x][y].append(z)

    nvocab, ntoken, PI = len(vocabs), len(tokens), list(PI)

    data = read_file(path.join(BASE_PATH, STOPWORDS_FILE))
    STOPWORDS = data and data.split('\n') or [ ]
    tfreq = [ ]
    for tok, _ in Counter(tokens).most_common(100):
      if tok not in STOPWORDS:
        tfreq.append(tok)

    ngram = NGram()
    ngram.nsent  = nsent
    ngram.ntoken = ntoken
    ngram.nvocab = nvocab
    ngram.tfreq  = tfreq
    ngram.PI     = PI
    ngram.T2     = T2
    ngram.T3     = T3
    return ngram

  def save(self, fp):
    pkl = {
      'nsent':  self.nsent,
      'ntoken': self.ntoken,
      'nvocab': self.nvocab,
      'tfreq':  self.tfreq,
      'PI':     self.PI,
      'T2':     self.T2,
      'T3':     self.T3,
    }
    with open(fp, 'wb') as fh:
      pickle.dump(pkl, fh)

  def gen_2gram_sent(self):
    x = random.choice(self.PI)
    sent = ''
    while True:
      Y = self.T2[x]
      sent += x
      if not len(Y): break
      x = random.choice(Y)
    return sent

  def gen_3gram_sent(self):
    x = random.choice(self.PI)
    y = random.choice(list(self.T3[x].keys()))
    sent = ''
    while True:
      Z = self.T3[x][y]
      sent += x
      if not len(Z): break
      x = y
      y = random.choice(Z)
    return sent

class App:

  def __init__(self):
    self.T = { }                # config db
    self.projects = { }         # project cache, { 'proj_name': { ... }, }
    self.cur_project = { }      # keys: 'proj_name', 'corpus_dp', 'corpus_fp', 'model_fp', 'model'

    self.setup_gui()
    self.setup_workspace()

    try: tk.mainloop()
    except KeyboardInterrupt: pass
    finally: self.save_workspace()

  def setup_gui(self):
    # root window
    wnd = tk.Tk()
    wnd.title(WINDOW_TITLE)
    (wndw, wndh), scrw, scrh = WINDOW_SIZE, wnd.winfo_screenwidth(), wnd.winfo_screenheight()
    wnd.geometry('%dx%d+%d+%d' % (wndw, wndh, (scrw - wndw) // 2, (scrh - wndh) // 4))
    wnd.resizable(False, False)
    wnd.protocol('WM_DELETE_WINDOW', wnd.quit)     # make sure close window leading to app exit
    self.wnd = wnd

    # font
    ft = tkfont.Font(family='Courier New', size=12)
    
    # main menu bar
    menu = tk.Menu(wnd, tearoff=False)
    wnd.config(menu=menu)
    self.menu = menu
    if True:
      sm = tk.Menu(menu, tearoff=False)
      sm.add_command(label="New..", command=self.project_new)
      sm.add_separator()
      sm.add_command(label="Exit", command=wnd.quit)
      menu.add_cascade(label="Project", menu=sm)
      
      sm = tk.Menu(menu, tearoff=False)
      sm.add_command(label="Merge corpus.txt", command=self.corpus_collect)
      sm.add_command(label="Edit corpus.txt..", command=self.corpus_edit)
      sm.add_command(label="Build model.pkl", command=self.model_build)
      sm.add_separator()
      var = tk.StringVar(wnd, value=ALGORITHM_TYPE)
      self.var_algorithm = var
      sm.add_radiobutton(label="2-gram", variable=var, value='2-gram')
      sm.add_radiobutton(label="3-gram", variable=var, value='3-gram')
      menu.add_cascade(label="Model", menu=sm)
      
      menu.add_command(label="Help", command=lambda: tkmsg.showinfo("Help", "I'm sorry but, this fucking world has no help :<"))

    # top: model select
    frm11 = ttk.Frame(wnd)
    frm11.pack(side=tk.TOP, anchor=tk.N, fill=tk.X)
    if True:
      ttk.Label(frm11, text="Model: ").pack(side=tk.LEFT, anchor=tk.W)
      ttk.Button(frm11, text="Spake!", width=8, command=self.hitokoto).pack(side=tk.RIGHT, anchor=tk.E)
      ttk.Button(frm11, text="Select..", width=6, command=self.project_select).pack(side=tk.RIGHT)

      var = tk.StringVar(wnd, value="")
      self.var_model_fp = var
      et = ttk.Entry(frm11, textvariable=var, state='readonly')
      et.pack(fill=tk.X, padx=2, pady=2)
    
    # middle: main panel
    frm12 = ttk.Frame(wnd)
    frm12.pack(fill=tk.X, expand=tk.YES)
    if True:
       tx = tkscrtxt.ScrolledText(frm12, background='#FFF', font=ft)
       tx.pack(fill=tk.BOTH, expand=tk.YES)
       self.tx = tx

    # bottom: status bar
    frm13 = ttk.Frame(wnd)
    frm13.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X)
    if True:
      var = tk.StringVar(wnd, "OK")
      self.var_stat_msg = var
      ttk.Label(frm13, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)
  
  def setup_workspace(self):
    fp = path.join(BASE_PATH, CONFIG_FILE)
    if path.exists(fp):
      try:
        with open(fp) as fh:
          self.T = json.load(fh)    # config db
      except json.JSONDecodeError:
        pass

    projname = self.T.get('recent-porject')
    if projname: self.project_select(projname)
  
  def save_workspace(self):
    self.T['recent-porject'] = self.cur_project.get('proj_name') or ''
    self.T['projects'] = {k: v.get('corpus_dp') for k, v in self.projects.items()}
    with open(path.join(BASE_PATH, CONFIG_FILE), 'w+') as fh:
      json.dump(self.T, fh, indent=2)

  def project_new(self):
    dp = tkfiledlg.askdirectory(initialdir=BASE_PATH)
    if not dp: return

    projname = path.basename(dp)
    if projname not in self.projects:
      self.cur_project = {
        'proj_name': projname, 
        'corpus_dp': dp,
        'corpus_fp': path.join(BASE_PATH, CORPUS_DIR, projname + '.txt'),
        'model_fp': path.join(BASE_PATH, MODEL_DIR, projname + '.pkl'),
        'model': None,
      }
      self.projects[projname] = self.cur_project
      self.var_stat_msg.set("Project %r created/opened" % projname)

    self.project_select(projname)

  def project_select(self, projname=None):
    if not projname:
      fp = tkfiledlg.askopenfilename(initialdir=BASE_PATH)
      if not fp: return
      projname = path.splitext(path.basename(fp))[0]

    self.tx.delete(0.0, tk.END)
    pkl_fp = path.join(BASE_PATH, MODEL_DIR, projname + '.pkl')
    if projname in self.projects:
      self.cur_project = self.projects.get(projname)   # use local cached
      ngram = self.cur_project.get('model')
    else:
      ngram = NGram(pkl_fp)                         # load
      self.cur_project = {                          # switch to
        'proj_name': projname,
        'corpus_dp': self.T.get('projects').get(projname),
        'corpus_fp': path.join(BASE_PATH, CORPUS_DIR, projname + '.txt'),
        'model_fp': pkl_fp,
        'model': ngram,
      }
      self.projects[projname] = self.cur_project    # cache it

    self.var_model_fp.set(pkl_fp)
    if ngram:
      _info = 'Model %r loaded, nsent/nvcb/ntok = %s/%s/%s' % (projname, ngram.nsent, ngram.nvocab, ngram.ntoken)
      self.var_stat_msg.set(_info)

  def corpus_collect(self):
    dp = self.cur_project.get('corpus_dp')
    if not dp: return

    sents = set()
    for fn in os.listdir(dp):
      if not fn.lower().endswith('.txt'): continue
      data = read_file(path.join(dp, fn))
      for line in data.split('\n'):
        ln = line.strip()
        if str.isdigit(ln): continue
        if len(ln) < 8: continue
        sents.add(ln)

    sents = sorted(list(sents))
    fp = self.cur_project.get('corpus_fp')
    with open(fp, 'w+') as fh:
      for sent in sents:
        fh.write(sent)
        fh.write('\n')
    
    tkmsg.showinfo('OK', 'Corpus of %r merged to %r' % (
      self.cur_project.get('proj_name'), self.cur_project.get('corpus_fp')))

  def corpus_edit(self):
    fp = self.cur_project.get('corpus_fp')
    if not fp: return

    os.system(fp)

  def model_build(self):
    fp = self.cur_project.get('corpus_fp')
    if not fp: return
    if not path.exists(fp):
      tkmsg.showerror("Error", "Cannot find corpus, model build failed.")
      return

    ngram = NGram.create_model(fp)
    ngram.save(self.cur_project.get('model_fp'))
    self.cur_project['model'] = ngram

    projname = self.cur_project.get('proj_name')
    tkmsg.showinfo('OK', 'Model %r saved to %r' % (projname, self.cur_project.get('model_fp')))
    
    _info = 'Model %r loaded, nsent/nvcb/ntok = %s/%s/%s' % (projname, ngram.nsent, ngram.nvocab, ngram.ntoken)
    self.var_stat_msg.set(_info)

  def hitokoto(self) -> str:
    m = self.cur_project.get('model')
    if not m:
      tkmsg.showerror("Error", "build your model first")
      return

    sent = None
    mt = self.var_algorithm.get()
    if   mt == '2-gram': sent = m.gen_2gram_sent()
    elif mt == '3-gram': sent = m.gen_3gram_sent()

    if sent:
      self.tx.delete(0.0, tk.END)
      self.tx.insert(0.0, sent)

# main
if __name__ == "__main__":
  os.chdir(BASE_PATH)
  for dp in [CORPUS_DIR, MODEL_DIR]:
    if not path.exists(dp): os.mkdir(dp)

  App()
