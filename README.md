## Quickstart
```sh 
sudo apt install -y python3 python3-pip
pip3 install -r requirements.txt
bash start

# input table as this
word1|translation1,word2|translation2,word3|translation3

# or as this (without translations)
word1,word2,word3
```


## example list backup syntax:
Backups are stored in a file named `neoanki_backup.json`. Its backup is stored in `neoanki_backup.json.bak` for verification purposes in case anything goes wrong with IO operations and try catch blocks fail to prevent that.
```JSON
{
  "testtable1": {
    "table": [
      [
        "on",
        "彼 (かれ kare)"
      ],
      [
        "ona",
        "彼女 (かのじょ kanojo)"
      ],
    ],
    "to_repeat": [
      [
        "ona",
        "彼女 (かのじょ kanojo)"
      ],
    ]
  },
  "testtable2": {
    "table": [
      [
        "literatura",
        "文学 (ぶんがく bungaku)"
      ],
      [
        "historia",
        "歴史 (れきし rekishi)"
      ],
    ],
    "to_repeat": []
  }
}    
```
