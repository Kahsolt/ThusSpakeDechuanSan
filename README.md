# Thus Spake Dechuan-San

    Dechuan-San (德川先生) was, is, and will be our lovable & wisable friend, 
    thus we'd always listen to His Oracle with highest pure sincerity.

----

### 怪话生成器

给定txt文本，使用ngram模型帮你自动生成怪话 :(  

Note: **txt文本必须是UTF8或者ASCII编码**  


### 怎么搞

  0. 运行 `python oracle.py`
  1. 建立工程：`Project - New..`，输入工程名即可、将保存为`projects/工程名.tsp`
    - 或打开已有工程：`Project - Open..`
  3. 生成语料库：`Model - Setup corpus-*.txt`，点击`Add..`加入文本文件、也可以手动输入每行一个路径，然后按`OK`保存，将整合成语料库`corpora/工程名.txt`
    - 若要手动检查语料库，`Model - Edit corpora.txt..` 可以直接编辑它
  4. 生成模型：`Model - Build model.pkl`，模型文件将保存在`models/工程名.pkl`
  5. 生成怪话：按钮 `Spake!`
    - 勾选 `Config - keep probaility` 时生成更接近原文，取消勾选则更怪话
    - 选择 `Config - 3-gram` 时生成更接近原文，`2-gram` 则更怪话


### 目录结构

- oracle.py          主脚本
- qqlog2sents.py     辅助脚本，qq记录抽取出txt
- projects/*.tsp     工程文件
- corpus/*.txt       源语料库
- corpra/*.txt       合并后的语料库(每个tsp工程对应一个合并后的语料库)
- models/*.pkl       模型文件


### requirements

  - jieba

----

by Armit
2020/02/16 
2020/02/26
