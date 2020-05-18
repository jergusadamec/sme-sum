# SME SUM - Dataset Build
-------

## Overview
The purpose of this project is to create a dataset of news sites that are 
obtained from the SME news web portal.
<!--Our work is highly inspired by work of NLP Group at the University of Edinburgh https://github.com/EdinburghNLP/XSum/tree/master/XSum-Dataset. -->



## Installation
Note: _Required Python 3+_;

First of all you need to install and create python virtual environment (venv).


```shell script
$ python3 -m venv venv
```

After that, activate venv.
```shell script
$ source venv/bin activate
```

Install all required packages.
```shell script
$ pip install -r requirements.txt
```

## Building the SME Dataset
The implementation process of building the data is realized by three following 
steps: getting the data, parsing the data and finally postprocessing the data.


1. **Obtain Sites from Wayback Archive**
   
   ```shell script
    $ python sme_archive_downloader.py --output-file-archive-url sme-archive-urls.txt --sme-content-menu-url https://www.sme.sk/najnovsie?page={} --wayback-archive-api-url https://archive.org/wayback/available?url={} --n-thread 10 --start-page-number 100 --end-page-number 12500
   ```

2. **Extract Reasonable Text from Sites**

   ```shell script
   $ python sme_archive_parser.py --input-file-archive-url sme-archive-urls.txt --output-dir-extracted-raw-content /sme-archive-extracted-raw-content --output-file-archive-premium-url sme-archive-urls-premium.txt --output-file-archive-failed-url sme-archive-urls-failed.txt --n-thread 10
   ```
   
3. **Postprocessing - Sentence Segmentation, Tokenization and Stemmatization/Lemmatization**
   
   ```shell script
   $ python sme_archive_postprocessing.py --input-dir-extracted-raw-content /sme-archive-extracted-raw-content --output-dir-preprocessed /sme-archive-preprocessed --stop_words_sk stop-words-sk.txt --n-thread 10
   ```
