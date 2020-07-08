# Thus Spake Dechuan-San

    Dechuan-San (德川先生) was, is, and will be our lovable & wisable friend, 
    thus we'd always listen to His Oracle with highest pure sincere.

----

### 怪话生成器

给定txt文本，使用ngram模型帮你自动生成怪话 :(
Note: **txt文本必须是UTF8或者ASCII编码**

### 怎么搞

  0. 运行 `python oracle.py`
  1. 准备源文本：任意路径新建一个文件夹、名字为 **工程名** ，把原始语料的txt文本全部丢进去
  2. 建立工程：`Project - New..` 选择你刚才的工程文件夹
    - 若要重新打开已经建模过的旧工程，直接 `Select..` 打开模型文件即可
  3. 生成语料库：`Model - Merge corpus.txt` 会把源语料合并排序，在`corpus`目录下生成`工程名.txt`语料库文件
    - 如果你要手动检查建模的语料库，直接编辑它 `Model - Edit corpus.txt..`
  4. 生成模型：`Model - Build model.pkl` 会对语料库建模，在`models`目录下生成`工程名.pkl`模型文件
  5. 生成怪话：点击按钮 `Spake!`
    - 修改 `Model - 2-gram/3-gram` 切换句子生成算法

### requirements

  - jieba

----

by Armit
2020/02/16 
2020/02/26
