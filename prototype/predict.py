from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import pickle
from sklearn.svm import SVC
import json
import jieba

if __name__=="__main__":
#   load the models
    word_vectors = Doc2Vec.load("trained_model_word2vector")
    with open('trained_model_SVM.pickle', 'rb') as f:
        svclassifier = pickle.load(f)


#   setup stop word as a set
    stop_list = set()
    with open("stopwords.txt", "r", encoding = "utf-8") as stopwords:
        for stopword in stopwords:
            stop_list.add(stopword.strip('\n'))

#   load special word dictionary to jieba
    jieba.load_userdict("dict.txt")
    documents = []
    with open("user_comments.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)


    with open("testset.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)

    true_positive = 0
    false_negative = 0
    false_positive = 0
    true_negative = 0
    counter = 0
    for user_comment in data["user_comments"]:
        label = user_comment["isTroll"]
        if user_comment["isTroll"] is True:
            label = 1
        else:
            label = 0
        cut_list =  list(jieba.cut(user_comment["comments"], cut_all = False))
        words = []
        for word in cut_list:
            if word not in stop_list:
                words.append(word)
        vector = word_vectors.infer_vector(words)
        predict = svclassifier.predict([vector])
        if label == 1 and predict == 1:
            true_positive = true_positive + 1
        elif label == 1 and predict == 0:
            false_negative = false_negative + 1
        elif label == 0 and predict == 1:
            false_positive = false_positive + 1
        elif label == 0 and predict == 0:
            true_negative = true_negative +1
        counter = counter + 1
    precision = true_positive/(true_positive+false_positive)
    recall = true_positive/(true_positive+false_negative)
    print ("Total ", counter, "accounts in test set.")
    print ("Precision:", precision)
    print ("Recall:", recall)