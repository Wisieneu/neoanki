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
Backups are stored in a file named `neoanki_backup.json`. Its backup is stored in `neoanki_backup.json.bak` for verification purposes.
```JSON
{
  "dd1-r1.1 2026-02-18 06-06": [
    [
      "on",
      "彼 (かれ kare)"
    ],
    [
      "ona",
      "彼女 (かのじょ kanojo)"
    ],
  ],
  "dd1-r1.3 2026-02-18 06-07": [
    [
      "literatura",
      "文学 (ぶんがく bungaku)"
    ],
    [
      "historia",
      "歴史 (れきし rekishi)"
    ],
  ]
}    
```
