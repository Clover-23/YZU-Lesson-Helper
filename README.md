# YZU Lesson Helper

## 聲明
本專案為作者學習用途，歡迎參考與學習。
若要使用請謹慎，所有後果自行承擔。

## 介紹
**YZU Lesson Helper 元智選課機器人 - 小幫手** 專為抽課苦手而設計，抽課的時候總是運氣很差，又難以抽空打開選課系統查看修課人數時，藉由此機器人幫助選課，以節省時間成本，當有空缺時能比一般人更容易加選到該門課，還有查詢課程資訊的功能，能接上其他的應用，比如Discord Bot 或是 Line Bot。

## Python版本及套件
Python 3.9.10
requests, lxml, BeautifulSoup4, tensorflow, opencv-python, numpy
進入環境後，使用pip安裝套件

    pip install --upgrade pip
    pip install numpy requests lxml BeautifulSoup4 tensorflow opencv-python

## 使用說明

請注意 **SETTING txt** 及 **data-input txt**

> **SETTING.txt**

    [Setting]
    # 是否開啟選課功能 0 為 off, 1 為 on
    select-lesson-mode = 0
    # 是否開啟儲存課程資訊功能
    get-lesson-info-mode = 1
    
    # 每一輪間隔的時間
    delay-per-cycle = 1.8
    # 每選一門課之間的間隔時間
    delay-per-lesson = 1.2
    # 帳號密碼以及欲選的課
    input-file-name = data-input.txt
    # 課程資訊輸出處
    output-file-name = lessons.csv

> **data-input.txt**
    
    s1234567
    password
    304:CS310A
    304:CS332A
    
   該檔案的檔名依照SETTING的定義，亦可以自訂。
   第一行為**s加上學號**，
   第二行為**密碼**。
   **課程不限個數**，可一直往下延伸，**數量少效果佳**。
   半形冒號前面為**系所編號**，後面為**課號加班級編號**。

套件安裝成功，上方設定完成後，確認終端機在專案目錄中（或使用其他方式）執行

    python main.py

