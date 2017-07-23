import numpy as np;
from numpy import linalg as LA;
from ..wishart import invwishart;

class DiffPrivImpl(object):
    @classmethod
    def SymmGaussian(cls,epsilon,delta,dimension,deltaF=1):
        standardDeviation = np.sqrt(2*np.log(1.25/delta))*deltaF/epsilon;
        print "Gaussian Standard deviation is %f." % standardDeviation;
        noiseMatrix = np.random.normal(0, standardDeviation, (dimension,dimension));
        #Copy upper triangle to lower triangle in a matrix.
        i_lower = np.tril_indices(dimension, -1);
        noiseMatrix[i_lower] = noiseMatrix.T[i_lower];
        
        #print noiseMatrix;
        return noiseMatrix;
    
    @classmethod
    def SymmWishart(cls,epsilon,dimension):
        df = dimension+1;
        sigma = 1/epsilon*np.identity(dimension);
        #print sigma;
        wishart = invwishart.wishartrand(df,sigma);
        #print wishart;
        return wishart;
    
    @classmethod
    def SymmWishart_withDelta(cls,epsilon,delta,dimension,sensitivity):
        df = dimension+int(np.floor(14.0/(epsilon*epsilon)*(2.0*np.log(4.0/delta))));
        sigma = (sensitivity*sensitivity)*np.identity(dimension);
        #print sigma;
        wishart = invwishart.wishartrand(df,sigma);
        #print wishart;
        return wishart;
    