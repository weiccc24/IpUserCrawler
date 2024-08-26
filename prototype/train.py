from gensim.test.utils import common_texts
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.svm import SVC
import pickle

if __name__=="__main__":
#   word2vector
    raw = open('segmentation.txt', 'r')
    documents = []
    for line in raw:
        cut = line.split()
        documents.append(TaggedDocument(cut[1:], [cut[0]]))
    model = Doc2Vec(vector_size=50, min_count=2, epochs=40)
    model.build_vocab(documents)
    model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)

    model.save("trained_model_word2vector")
#   SVM
    vecs = []
    labels = []
    raw = open('segmentation.txt', 'r')
    for line in raw:
        cut = line.split()
        labels.append(int(cut[0]))
        vecs.append(model.infer_vector(cut[1:]))

    svclassifier = SVC(kernel='rbf', gamma='auto')  
    svclassifier.fit(vecs, labels)

#   Save the model.
    with open('trained_model_SVM.pickle', 'wb') as f:
        pickle.dump(svclassifier, f)