NLP_name_extraction_and_emotion_analysis
=====
An algorithm mainly bases on the hanlp and snownlp and be applied to actors'name extraction and emotion analysis.<br>
Training data roots in comments from movie forum or social platform.

Main codes
-----
* hanlp.java

    Using `hadoop` to process big data,including get data from database and call jar of hanlp to do the word segementation.<br><br>
    It's OK if you don't know how to run a hadoop project.`Hanlp` has supported both python and java.This file just do the word segementation of the movie comments we acquired before. `What you have to do is to write the appropriate program using the CRF algorithm and HMM algorithm of the hanlp to get the Name sequence and Proper noun sequence.`<br><br>

* name_extraction.py

    Using editDistance and jaccardDistance , web searching to extract actor's name from extraction and build the mapping of the actors and nicknames.
    
*  emotion_analysis.py
    
    Using snownlp to analysis the emotion of the both total sentences and short_cut_sentences of the comments.Coming up a sum score of an actor in the specific movie.
    
Operation Environment
------
* HADOOP(not nessary if your data isn't so big)
* HANLP
* SNOWNLP
* MYSQLDB(not nessary if your data doesn't come from db)

Operation Instruction
------
* first step<br>
running hanlp.java on hadoop,save the result in a appropriate path.

* second step<br>
running name_extraction.py，new a forder to save the json file you get.

* third step<br>
running emotion_analysis.py，new a forder to save the json file you get.

Output instance
------
* Output of hanlp.java——人名序列example
* Output of name_extraction.py——movie_actor_nick_2018_example/...json
* Output of emotion_analysis.py——movie_actor_score_2018_example/...json
