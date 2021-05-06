#!/usr/bin/env python3w
# Author: Armit
# Create Time: 2020/02/16 
# Update Time: 2021/05/06 

import os
from os import path
import re
import json
import pickle
from random import choice, random
from collections import Counter, defaultdict

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import tkinter.messagebox as tkmsg
import tkinter.simpledialog as tkdlg 
import tkinter.filedialog as tkfiledlg
import tkinter.scrolledtext as tkscrtxt

import jieba


__version__ = '0.2'

# settings
BASE_PATH = path.dirname(path.abspath(__file__))
PROJECTS_PATH = path.join(BASE_PATH, 'projects')
CORPUS_PATH = path.join(BASE_PATH, 'corpus')
CORPORA_PATH = path.join(BASE_PATH, 'corpora')
MODELS_PATH = path.join(BASE_PATH, 'models')
CONFIG_FILE = path.join(BASE_PATH, 'config.json')


WINDOW_TITLE = "Thus Spake Dechuan-san (Ver %s)" % __version__
WINDOW_SIZE = (400, 500)
SUB_WINDOW_TITLE = "Setup corpus list..."
SUB_WINDOW_SIZE = (600, 250)

ALGORITHM_TYPE = '2-gram'   # ['2-gram', '3-gram']
KEEP_PROBABILITY = True


REGEX_WHITESPACE = re.compile(r'\s+')
REGEX_BOM = re.compile(r'\ufeff')
REGEX_EOS = re.compile(r'。')


# sysfix & utils
def open(fp:str, rw='r', **kwargs):
  from builtins import open as _open
  return 'b' in rw and _open(fp, rw, **kwargs) or _open(fp, rw, encoding='utf8', **kwargs)

def read_file(fp:str) -> str:
  def fuck_encoding(bdata:bytes) -> str:
    for encoding in ['gb18030', 'ascii', 'utf8']:
      try: return bdata.decode(encoding)
      except UnicodeDecodeError: pass
    raise UnicodeDecodeError
  with open(fp, 'rb') as fp:
    return fuck_encoding(fp.read())

def preprocess(fp:str) -> str:    # read a file spilt sentence and do some cleaning
  data = read_file(fp).strip()
  data = REGEX_BOM.sub('', data)
  data = REGEX_WHITESPACE.sub('\n', data)
  data = REGEX_EOS.sub('。\n', data)
  lines = ['']
  for line in data.split('\n'):
    line = line.strip()
    if len(line) + len(lines[-1]) <= 20:
      lines[-1] += line
    else:
      lines.append(line)
  return '\n'.join(lines)


# app
class Project:   # the project.tsp file

  def __init__(self, name, corpus_fps:[str]=[]):  # create new project with settings
    self.name = name
    self.corpus_fps = corpus_fps
    self.corpora_fp = path.join(CORPORA_PATH, name + '.txt')
    self.model_fp = path.join(MODELS_PATH, name + '.pkl')

  def update(self, corpus_fps:[str]):    # update settings
    self.corpus_fps = corpus_fps
    self.make_corpora()
  
  def make_corpora(self):     # merge all corpus-*.txt to corpora.txt
    with open(self.corpora_fp, 'w') as fh:
      for fp in self.corpus_fps:
        fh.write(preprocess(fp))

  @classmethod
  def load(cls, fp:str):     # load project.tsp to prj
    with open(fp) as fh:
      tsp = json.load(fh)

    prj = cls(tsp.get('name'), tsp.get('corpus_fps'))
    return prj
  
  def save(self, fp:str):    # save prj to project.tsp
    tsp = {
      'name': self.name,
      'corpus_fps': self.corpus_fps,
      'corpora_fp': self.corpora_fp,
      'model_fp': self.model_fp,
    }
    with open(fp, 'w') as fh:
      json.dump(tsp, fh, ensure_ascii=False, indent=2)

class NGram:     # the model.pkl file

  def __init__(self):
    self.PI = None   # {'x'}, init words
    self.T2 = None   # {'x': {'y': prob}}, 2-gram transfer matrix
    self.T3 = None   # {'x': {'y': {'z': prob}}}, 3-gram transfer matrix

  @classmethod
  def _ctor1(cls): return defaultdict(int)
  @classmethod
  def _ctor2(cls): return defaultdict(NGram._ctor1)

  def build_model(self, corpora_fp:str):   # build ngram from corpora

    PI = set()
    T2, T3 = defaultdict(NGram._ctor1), defaultdict(NGram._ctor2)

    with open(corpora_fp) as fh:
      for line in fh.readlines():
        toks = jieba.lcut(line)
        if len(toks) <= 2: continue
        
        PI.add(toks[0])     # init token
        for x, y in zip(toks, toks[1:]):
          T2[x][y] += 1
        for x, y, z in zip(toks, toks[1:], toks[2:]):
          T3[x][y][z] += 1

    # convert cnt to prob
    for cntr in T2.values():
      cnt = sum(cntr.values())
      for y in cntr.keys():
        cntr[y] /= cnt
        assert 0.0 <= cntr[y] <= 1.0
    for _ in T3.values():
      for cntr in _.values():
        cnt = sum(cntr.values())
        for z in cntr.keys():
          cntr[z] /= cnt
          assert 0.0 <= cntr[z] <= 1.0
    
    self.PI = list(PI)
    self.T2 = T2
    self.T3 = T3

  @classmethod
  def load(cls, fp:str):    # load model.pkl to ngram
    with open(fp, 'rb') as fh:
      pkl = pickle.load(fh)
    
    ngram = cls()
    ngram.PI = pkl.get('PI')
    ngram.T2 = pkl.get('T2')
    ngram.T3 = pkl.get('T3')
    return ngram
  
  def save(self, fp:str):            # save ngram to model.pkl
    pkl = {
      'PI': self.PI,
      'T2': self.T2,
      'T3': self.T3,
    }
    with open(fp, 'wb') as fh:
      pickle.dump(pkl, fh)

  def _choose_word(self, pdf, keep_prob):
    if keep_prob:
      r = random()
      p_cont = 0.0
      for z in sorted(pdf.keys()):
        p_cont += pdf[z]
        if p_cont >= r: return z
    else:
      return choice(list(pdf.keys()))  # otherwise or in case random() fails

    raise ValueError  # shouldn't reach here

  def gen_2gram_sent(self, keep_prob=KEEP_PROBABILITY):
    x = choice(self.PI)
    sent = ''
    while True:
      sent += x
      Y = self.T2[x]
      if not len(Y): break
      x = self._choose_word(Y, keep_prob)        # shift right
    return sent

  def gen_3gram_sent(self, keep_prob=KEEP_PROBABILITY):
    x = choice(self.PI)
    y = choice(list(self.T3[x].keys()))
    sent = ''
    while True:
      sent += x
      Z = self.T3[x][y]
      if not len(Z): break
      x, y = y, self._choose_word(Z, keep_prob)  # shift right
    return sent

def require_project(fn):
  def wrapper(app, *args, **kwargs):
    if not app.project:
      app.var_stat_msg.set(f"Error: no current project to work on.")
      return
    return fn(app, *args, **kwargs)
  return wrapper

class App:

  def __init__(self):
    self.project_fp = None    # str
    self.project = None       # Project
    self.model = None         # NGram

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
    wnd.bind("<Control S>", self.project_save)
    wnd.protocol('WM_DELETE_WINDOW', wnd.quit)     # make sure close window leading to app exit
    self.wnd = wnd


    # font
    ft = tkfont.Font(family='Courier New', size=12)
    sft = tkfont.Font(family='Courier New', size=8)
    
    # main menu bar
    menu = tk.Menu(wnd, tearoff=False)
    wnd.config(menu=menu)
    self.menu = menu
    if True:
      if True:
        sm = tk.Menu(menu, tearoff=False)
        sm.add_command(label="New..", command=self.project_new)
        sm.add_command(label="Open..", command=self.project_open)
        sm.add_separator()
        sm.add_command(label="Save", command=self.project_save)
        sm.add_separator()
        sm.add_command(label="Exit", command=wnd.quit)
        menu.add_cascade(label="Project", menu=sm)
      
      if True:
        sm = tk.Menu(menu, tearoff=False)
        sm.add_command(label="Setup corpus-*.txt", command=lambda: self.corpus_setup('show'))
        sm.add_command(label="Build model.pkl", command=self.model_build)
        sm.add_separator()
        sm.add_command(label="Edit corpora.txt..", command=self.corpora_edit)
        menu.add_cascade(label="Model", menu=sm)
  
      if True:
        sm = tk.Menu(menu, tearoff=False)
        var = tk.BooleanVar(wnd, value=KEEP_PROBABILITY)
        self.var_keep_prob = var
        sm.add_checkbutton(label='keep probability', variable=var)
        sm.add_separator()
        var = tk.StringVar(wnd, value=ALGORITHM_TYPE)
        self.var_algorithm = var
        sm.add_radiobutton(label="2-gram", variable=var, value='2-gram')
        sm.add_radiobutton(label="3-gram", variable=var, value='3-gram')
        menu.add_cascade(label="Config", menu=sm)
  
      if True:
        menu.add_command(label="Help", command=lambda: tkmsg.showinfo("Help", "I'm sorry but, this fucking world has no help :<"))

    # top: model select
    frm11 = ttk.Frame(wnd)
    frm11.pack(side=tk.TOP, anchor=tk.N, fill=tk.X)
    if True:
      ttk.Button(frm11, text="Spake!", width=8, command=self.hitokoto).pack(side=tk.RIGHT, anchor=tk.E)
    
    # middle: main panel
    frm12 = ttk.Frame(wnd)
    frm12.pack(fill=tk.BOTH, expand=tk.YES)
    if True:
       tx = tkscrtxt.ScrolledText(frm12, background='#FFF', font=ft)
       tx.pack(fill=tk.BOTH, expand=tk.YES)
       self.tx = tx

    # bottom: status bar
    frm13 = ttk.Frame(wnd)
    frm13.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X)
    if True:
      var = tk.StringVar(wnd, "Init.")
      self.var_stat_msg = var
      ttk.Label(frm13, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)
  
    # sub window
    subwnd = tk.Toplevel()
    subwnd.title(SUB_WINDOW_TITLE)
    (wndw, wndh), scrw, scrh = SUB_WINDOW_SIZE, subwnd.winfo_screenwidth(), subwnd.winfo_screenheight()
    subwnd.geometry('%dx%d+%d+%d' % (wndw, wndh, (scrw - wndw) // 2, (scrh - wndh) // 4))
    subwnd.resizable(False, False)
    subwnd.protocol('WM_DELETE_WINDOW', lambda: self.corpus_setup('ok'))  # make sure close window leading to save list
    subwnd.withdraw()
    self.subwnd = subwnd

    sfrm11 = ttk.Frame(subwnd)
    sfrm11.pack(side=tk.TOP, expand=tk.YES)
    if True:
       tx = tkscrtxt.ScrolledText(sfrm11, background='#FFF', font=sft, height=12)
       tx.pack(fill=tk.X, expand=tk.YES)
       self.tx_corpus = tx

    sfrm12 = ttk.Frame(subwnd)
    sfrm12.pack(side=tk.BOTTOM, expand=tk.YES)
    if True:
      ttk.Button(sfrm12, text="Add..", width=8, command=lambda: self.corpus_setup('add')).pack(side=tk.LEFT)
      ttk.Button(sfrm12, text="OK", width=8, command=lambda: self.corpus_setup('ok')).pack(side=tk.RIGHT)

  def setup_workspace(self):
    if path.exists(CONFIG_FILE):
      with open(CONFIG_FILE) as fh:
        cfg = json.load(fh)
      self.var_keep_prob.set(cfg.get('keep_prob'))
      self.var_algorithm.set(cfg.get('algorithm'))
      if cfg.get('project_fp'):
        self.project_open(cfg.get('project_fp'))
        self.tx.delete(0.0, tk.END)
        self.tx.insert(0.0, cfg.get('text'))

  def save_workspace(self):
    if self.project:
      self.project.save(self.project_fp)
    if self.model:
      self.model.save(self.project.model_fp)
    
    cfg = {
      'project_fp': self.project_fp,
      'keep_prob': self.var_keep_prob.get(),
      'algorithm': self.var_algorithm.get(),
      'text': self.tx.get(0.0, tk.END).strip(),
    }
    with open(CONFIG_FILE, 'w') as fh:
      json.dump(cfg, fh, ensure_ascii=False, indent=2)
  
  def project_open(self, fp=None):
    if not fp: fp = tkfiledlg.askopenfilename(title="Open a Project...",
                                              initialdir=PROJECTS_PATH, 
                                              filetypes=[('TSDS Project', '*.tsp'), ('All Files', '*')])
    if not fp: return

    try:
      self.project_fp = fp    # mem it for later save
      self.project = Project.load(fp)
      try: self.model = NGram.load(self.project.model_fp)
      except: self.model = NGram()

      self.tx.delete(0.0, tk.END)
      self.var_stat_msg.set(f'Project {self.project.name} opened')
    except Exception as e:
      self.var_stat_msg.set(f'Error: {e}')

  def project_new(self):
    name = tkdlg.askstring("New Project...", "Input project name: ")
    if not name: return

    self.project_fp = path.join(PROJECTS_PATH, name + '.tsp')
    self.project = Project(name)

    self.var_stat_msg.set(f"Project {self.project.name} created.")

  @require_project
  def project_save(self):
    self.project.save(self.project_fp)
    self.var_stat_msg.set(f"Project {self.project.name} saved.")

  def _corpus_tx_to_ls(self) -> [str]:
    return sorted(list({fp.strip() for fp in self.tx_corpus.get(0.0, tk.END).strip().split('\n') if fp.strip()}))

  def _corpus_ls_to_tx(self) -> None:
    self.tx_corpus.delete(0.0, tk.END)
    self.tx_corpus.insert(0.0, '\n'.join(self.project.corpus_fps or []))

  @require_project
  def corpus_setup(self, action):
    # update corpus list
    if action == 'show':
      self._corpus_ls_to_tx()
      self.subwnd.update()
      self.subwnd.deiconify()
    elif action == 'ok':
      self.subwnd.withdraw()
      corpus_fps = self._corpus_tx_to_ls()
      self.project.update(corpus_fps)
      self.var_stat_msg.set(f"Corpora of {self.project.name} generated.")
      tkmsg.showinfo("Success", "Corpora generated :)")
    elif action == 'add':
      fps = tkfiledlg.askopenfilenames(title="Open corpus texts...",
                                       initialdir=CORPUS_PATH, 
                                       filetypes=[('Text file', '*.txt'), ('All Files', '*')])
      if not fps: return
      self.project.corpus_fps += fps
      self.project.corpus_fps = sorted(list(set(self.project.corpus_fps)))
      self._corpus_ls_to_tx()

  @require_project
  def corpora_edit(self):
    if not path.exists(self.project.corpora_fp):
      tkmsg.showerror("Error", "setup corpus first")
      return

    os.system(self.project.corpora_fp)

  @require_project
  def model_build(self):
    fp = self.project.corpora_fp
    if not path.exists(fp):
      tkmsg.showerror("Error", "Cannot find corpora, model build failed.")
      self.var_stat_msg.set(f'Error, cannot find corpora, model build failed..')
      return

    self.model.build_model(fp)
    self.model.save(self.project.model_fp)
    self.var_stat_msg.set(f'Model of {self.project.name} built.')
    tkmsg.showinfo("Success", "Model build successfully :)")

  def hitokoto(self):
    m = self.model
    if not m:
      tkmsg.showerror("Error", "build model first")
      return

    sent = None
    ws = self.var_algorithm.get()
    kp = self.var_keep_prob.get()
    if   ws == '2-gram': sent = m.gen_2gram_sent(kp)
    elif ws == '3-gram': sent = m.gen_3gram_sent(kp)

    if sent:
      self.tx.delete(0.0, tk.END)
      self.tx.insert(0.0, sent)


# main
if __name__ == "__main__":
  os.chdir(BASE_PATH)
  for dp in [PROJECTS_PATH, CORPUS_PATH, CORPORA_PATH, MODELS_PATH]:
    os.makedirs(dp, exist_ok=True)

  App()
