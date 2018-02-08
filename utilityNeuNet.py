from keras.models import Sequential;
from keras.layers import Dense,Activation,Dropout;
from keras.utils import np_utils;
from keras import backend as K;
from keras.callbacks import Callback;

import tensorflow as tf;

from pkg.dimReduction import PCAModule;
from pkg.diffPrivDimReduction import DPModule;
from pkg.diffPrivDimReduction import DiffPrivPCAModule;
from pkg.global_functions import globalFunction as gf;

from sklearn.model_selection import StratifiedShuffleSplit;
from sklearn.model_selection import StratifiedKFold;
from sklearn import preprocessing;
from sklearn.preprocessing import StandardScaler;
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score;

import numpy as np;
from numpy import linalg as LA;
import sys;
import os;
from time import time;
import matplotlib.pyplot as plt;

###################################
# TensorFlow wizardry
config = tf.ConfigProto()
 
# Don't pre-allocate memory; allocate as-needed
config.gpu_options.allow_growth = True
 
# Only allow a total of half the GPU memory to be allocated
config.gpu_options.per_process_gpu_memory_fraction = 0.8
 
# Create a session with the above options specified.
K.tensorflow_backend.set_session(tf.Session(config=config))
###################################
'''
class Metrics_callback(Callback):
    def on_train_begin(self, logs={}):
        self.val_f1s = []
        self.val_recalls = []
        self.val_precisions = []
 
    def on_epoch_end(self, epoch, logs={}):
        #val_predict = (np.asarray(self.model.predict(self.validation_data[0]))).round()
        val_predict = self.model.predict_classes(self.validation_data[0]);
        val_targ = self.validation_data[1]
        _val_f1 = f1_score(val_targ, val_predict)
        _val_recall = recall_score(val_targ, val_predict)
        _val_precision = precision_score(val_targ, val_predict)
        self.val_f1s.append(_val_f1)
        self.val_recalls.append(_val_recall)
        self.val_precisions.append(_val_precision)
        print "--val_f1: %f , val_precision: %f , val_recall %f" % (_val_f1, _val_precision, _val_recall)
        return;

myCallback = Metrics_callback();

def f1(y_true, y_pred):
    def recall(y_true, y_pred):
        """Recall metric.

        Only computes a batch-wise average of recall.

        Computes the recall, a metric for multi-label classification of
        how many relevant items are selected.
        """
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
        recall = true_positives / (possible_positives + K.epsilon())
        return recall

    def precision(y_true, y_pred):
        """Precision metric.

        Only computes a batch-wise average of precision.

        Computes the precision, a metric for multi-label classification of
        how many selected items are relevant.
        """
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
        precision = true_positives / (predicted_positives + K.epsilon())
        return precision
    precision = precision(y_true, y_pred)
    recall = recall(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall));
'''


def drawF1Score(datasetTitle, data=None, path=None, figSavedPath=None):
    plt.clf();
    if path is not None:
        data = np.loadtxt(path, delimiter=",");
    numOfTrails = data.shape[0] / 10;
    print "Number of points on x-axis: %d" % numOfTrails;
    """
    minVector = np.amin(data[:,1:],axis=0);
    yMin = min(minVector);
    maxVector = np.amax(data[:,1:],axis=0);
    yMax = max(maxVector);

    yMin = (yMin-0.1) if (yMin-0.1)>0 else 0;
    yMax = (yMax+0.1) if (yMax+0.1)<1 else 1;
    #x = [10,40,70,100,130,160,190,220,250,280,310,340];
    y1Line,y2Line,y3Line = plt.plot(x, data[:,1], 'bo-', x, data[:,2], 'r^-',x, data[:,3], 'gs-');

    plt.legend([y1Line,y2Line,y3Line], ['PCA', 'Gaussian Noise','Wishart Noise'],loc=4);
    """
    x = np.arange(100,1100,100);
    targetDimension = 9;
    pcaF1 = data[targetDimension::20,3::3];
    dpdpcaF1 = data[targetDimension+1::20,4::3];
    minVector = np.amin(pcaF1, axis=0);
    yMin = min(minVector);
    maxVector = np.amax(dpdpcaF1, axis=0);
    yMax = max(maxVector);

    yMin = (yMin - 0.05) if (yMin - 0.05) > 0 else 0;
    yMax = (yMax + 0.05) if (yMax + 0.05) < 1 else 1.05;

    pcaF1Mean, pcaF1Std = gf.calcMeanandStd(np.asarray(pcaF1));
    pcaF1ErrorLine = plt.errorbar(x, pcaF1Mean, yerr=pcaF1Std, fmt='b', capsize=4);
    pcaF1Line, = plt.plot(x, pcaF1Mean, 'b-')

    dpdpcaF1Mean, dpdpcaF1Std = gf.calcMeanandStd(np.asarray(dpdpcaF1));
    dpdpcaF1ErrorLine = plt.errorbar(x, dpdpcaF1Mean, yerr=dpdpcaF1Std, fmt='r', capsize=4);
    dpdpcaF1Line, = plt.plot(x, dpdpcaF1Mean, 'r-')

    plt.axis([0, x[-1] + 100, yMin, yMax]);
    # plt.axis([0,10,0.4,1.0]);
    plt.legend([pcaF1Line, dpdpcaF1Line], ['PCA', 'DPDPCA'], loc=4);
    plt.xlabel('Number of Epochs', fontsize=18);
    plt.ylabel('F1-Score', fontsize=18);
    plt.title(datasetTitle, fontsize=18);
    plt.xticks(x);

    if figSavedPath is None:
        plt.show();
    else:
        plt.savefig(figSavedPath + "NN_" + datasetTitle + '.pdf', format='pdf', dpi=1000);



def build_MLP(numOfSamples,numOfFeatures,numOfOutputs):
    # alpha is in [2,10];
    alpha = 2;
    #DROPOUT = 0.1;
    #N_HIDDEN = numOfSamples/(alpha*(numOfFeatures+numOfOutputs));
    N_HIDDEN = numOfFeatures;
    print "neurons in hidden layer: %d" % N_HIDDEN;
    model = Sequential();
    model.add(Dense(N_HIDDEN, input_dim=numOfFeatures,activation='sigmoid'));
    #model.add(Activation('sigmoid'));
    #model.add(Dropout(DROPOUT));
    #model.add(Dense(N_HIDDEN,activation='relu'));
    #model.add(Activation('relu'));
    #model.add(Dropout(DROPOUT));
    model.add(Dense(1,activation='sigmoid'));
    #model.summary();
    # Compile model
    model.compile(loss='binary_crossentropy', optimizer='sgd', metrics=['accuracy'])
    #model.compile(loss='binary_crossentropy', optimizer='sgd', metrics=[f1])
    return model;

def fit_MLP(x_train,y_train,x_test,y_test):
    EPOCH = 100;
    BATCH_SIZE = 32;
    VALIDATION_SPLIT = 0.1;
    #RESHAPED = 856;
    #NB_CLASSES = 2;
    KFOLD_SPLITS = 5;
    # load pima indians dataset
    #dataset = numpy.loadtxt("pima-indians-diabetes.csv", delimiter=",")
    # split into input (X) and output (Y) variables
    #X = dataset[:,0:8]
    #Y = dataset[:,8]

    #y_train = np_utils.to_categorical(y_train,NB_CLASSES);
    #y_test = np_utils.to_categorical(y_test,NB_CLASSES);

    # good trick to change values in ndArray.
    # convert labels from [1,-1] to [1,0].
    y_train[y_train < 0]=0;
    y_test[y_test < 0]=0;
    model = build_MLP(x_train.shape[0],x_train.shape[1],1);
    # Fit the model
    expRes = [];
    init_weights = model.get_weights();
    epoches = np.arange(100,1100,100);
    for singleEpoch in epoches:
        skf = StratifiedKFold(n_splits=KFOLD_SPLITS, shuffle=True);
        res = [];
        for index, (train_indices_cv, val_indices_cv) in enumerate(skf.split(x_train, y_train)):
            x_train_cv, x_val_cv = x_train[train_indices_cv], x_train[val_indices_cv]
            y_train_cv, y_val_cv = y_train[train_indices_cv], y_train[val_indices_cv]
            #model = build_MLP(x_train_cv.shape[0],x_train_cv.shape[1],1);
            model.fit(x_train_cv, y_train_cv, epochs=singleEpoch, batch_size=BATCH_SIZE,verbose=0,validation_split = VALIDATION_SPLIT);
            # evaluate the model
            scores = model.evaluate(x_test, y_test);
            res.append(scores[1]);
            #print("\nCross validation-%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))
            y_pred = model.predict_classes(x_test);
            f1Score = f1_score(y_pred, y_test);
            res.append(f1Score);
            #print("Cross validation: f1 Score: %f, accuracy: %f." % (f1Score,scores[1]));
            model.set_weights(init_weights); 
        resArray = np.asarray(res);
        resArray = np.reshape(resArray,(-1,2));
        avgRes = np.mean(resArray,axis=0);
        print("Avg cross validation: epoch: %d, accuracy: %f, f1 Score: %f" % (singleEpoch, avgRes[0],avgRes[1]));
        expRes.append(singleEpoch);
        expRes.append(avgRes[0]);
        expRes.append(avgRes[1]);
    return expRes;

def singleExp(xDimensions,trainingData,testingData,largestReducedFeature,epsilon):
    pureTrainingData = trainingData[:,1:];
    trainingLabel = trainingData[:,0];
    
    pureTestingData = testingData[:,1:];
    testingLabel = testingData[:,0];

    scaler = StandardScaler(copy=False);
    #print pureTrainingData[0];
    scaler.fit_transform(pureTrainingData);
    #print pureTrainingData[0];

    #print pureTestingData[0];
    scaler.transform(pureTestingData);
    #print pureTestingData[0];

    cprResult = [];
    pcaImpl = PCAModule.PCAImpl(pureTrainingData);
    
    pcaImpl.getPCs(largestReducedFeature);
    numOfTrainingSamples = trainingData.shape[0];
    
    delta = np.divide(1.0,numOfTrainingSamples);
    print "epsilon: %.2f, delta: %f" % (epsilon,delta);
    
    isGaussianDist = True;
    dpGaussianPCAImpl = DiffPrivPCAModule.DiffPrivPCAImpl(pureTrainingData);
    dpGaussianPCAImpl.setEpsilonAndGamma(epsilon,delta);
    dpGaussianPCAImpl.getDiffPrivPCs(isGaussianDist,largestReducedFeature);
    
    for k, targetDimension in np.ndenumerate(xDimensions):    
        #print pcaImpl.projMatrix[:,0];
        #print k;
        cprResult.extend([targetDimension]);
        projTrainingData1 = pcaImpl.transform(pureTrainingData,targetDimension);
        projTestingData1 = pcaImpl.transform(pureTestingData,targetDimension);
        print "Non-noise PCA %d" % targetDimension;
        result = fit_MLP(projTrainingData1,trainingLabel,projTestingData1,testingLabel);
        
        cprResult.extend(result);

        projTrainingData2 = dpGaussianPCAImpl.transform(pureTrainingData,targetDimension);
        projTestingData2 = dpGaussianPCAImpl.transform(pureTestingData,targetDimension);
        print "Gaussian-noise PCA %d" % targetDimension;
        
        result = fit_MLP(projTrainingData2,trainingLabel,projTestingData2,testingLabel);
        
        cprResult.extend(result);
        """
        projTrainingData3 = dpWishartPCAImpl.transform(pureTrainingData,targetDimension);
        projTestingData3 = dpWishartPCAImpl.transform(pureTestingData,targetDimension);
        print "Wishart-noise PCA %d" % targetDimension;
        if isLinearSVM:
            result = SVMModule.SVMClf.linearSVM(projTrainingData3,trainingLabel,projTestingData3,testingLabel);
        else:
            result = SVMModule.SVMClf.rbfSVM(projTrainingData3,trainingLabel,projTestingData3,testingLabel);
        cprResult.append(result[3]);
        """

    resultArray = np.asarray(cprResult);
    resultArray = np.reshape(resultArray, (len(xDimensions), -1));
    return resultArray;

def doExp(datasetPath,epsilon,varianceRatio,numOfRounds,numOfDimensions):
    if os.path.basename(datasetPath).endswith('npy'):
        data = np.load(datasetPath);
    else:
        data = np.loadtxt(datasetPath, delimiter=",");
    scaler = StandardScaler();
    data_std = scaler.fit_transform(data[:,1:]);
    globalPCA = PCAModule.PCAImpl(data_std);

    numOfFeature = data.shape[1]-1;
    largestReducedFeature = globalPCA.getNumOfPCwithKPercentVariance(varianceRatio);
    print "%d/%d dimensions captures %.2f variance." % (largestReducedFeature,numOfFeature,varianceRatio);
    xDimensions = None;
    if numOfDimensions > numOfFeature:
        xDimensions = np.arange(1,numOfFeature);
        largestReducedFeature=numOfFeature;
    else:
        xDimensions = np.arange(10,largestReducedFeature,max(largestReducedFeature/numOfDimensions,1));
    cprResult = None;
    rs = StratifiedShuffleSplit(n_splits=numOfRounds, test_size=.15, random_state=0);
    rs.get_n_splits(data[:,1:],data[:,0]);

    for train_index, test_index in rs.split(data[:,1:],data[:,0]):
        trainingData = data[train_index];
        testingData = data[test_index];
        
        tmpResult = singleExp(xDimensions, trainingData, testingData, largestReducedFeature, epsilon);
        if cprResult is None:
            cprResult = tmpResult;
        else:
            cprResult = np.concatenate((cprResult,tmpResult),axis=0);


    for result in cprResult:
        print ','.join(['%.3f' % num for num in result]);

    return cprResult;
if __name__ == "__main__":
    numOfRounds = 3;
    resultSavedPath = "./log/";
    numOfDimensions = 10;
    epsilon = 0.3;
    varianceRatio = 0.8;
    
    if len(sys.argv) > 1:
        datasetPath = sys.argv[1];
        print "+++ using passed in arguments: %s" % (datasetPath);
        result = doExp(datasetPath,epsilon,varianceRatio,numOfRounds,numOfDimensions);
        np.savetxt(resultSavedPath+"numPC_NN_"+os.path.basename(datasetPath)+"_"+str(time())+".output",result,delimiter=",",fmt='%1.3f');
    else:
        datasets = ['CNAE_2'];
        #datasets = ['diabetes','Amazon_2','Australian','german','ionosphere'];
        for dataset in datasets:
            print "++++++++++++++++++++++++++++  "+dataset+"  +++++++++++++++++++++++++";
            datasetPath = "./input/"+dataset+"_prePCA";
            result = doExp(datasetPath,epsilon,varianceRatio,numOfRounds,numOfDimensions);
            np.savetxt(resultSavedPath+"numPC_NN_"+dataset+"_"+str(time())+".output",result,delimiter=",",fmt='%1.3f');