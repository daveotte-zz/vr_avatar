
import sys
import os
import data
from keras.models import Sequential
from keras.layers import Dense
import keras.optimizers
import numpy

# Initialize the script plug-in
def initializeNN():

    
    fbxManager = data.fbxManager('fbxGroups')
    nnDataConfigurations = data.nnDataConfigurations('nnDataConfigurations')
    nnDataObj = fbxManager.getNnDataObj(nnDataConfigurations.getObject('predictHip'))
    nnDataObj.write('/home/daveotte/work/output.csv')
    #nnDataObj.printData()
    print "inputStart: %d, inputEnd: %d, outputStart: %d, outputEnd: %d" % \
                                (nnDataObj.inputStart,
                                 nnDataObj.inputEnd,  
                                 nnDataObj.outputStart,
                                 nnDataObj.outputEnd)
    
    # fix random seed for reproducibility
    seed = 7
    numpy.random.seed(seed)

    dataset = numpy.loadtxt("/home/daveotte/work/output.csv", delimiter=",")
    # split into input (X) and output (Y) variables
    X = dataset[:,nnDataObj.inputStart:nnDataObj.inputEnd]
    Y = dataset[:,nnDataObj.outputStart:nnDataObj.outputEnd]
    #X = dataset[:,0:11]
    #Y = dataset[:,11:23]

    model = Sequential()

    inputDim = nnDataObj.inputEnd
    outputDim = (nnDataObj.outputEnd-nnDataObj.outputStart)
    print inputDim
    print outputDim
    #Dense:fully connected- arg1:number of nodes, input_dim(eq to number of input nodes
    #init:initialize network weights <default is 0 and .05), activation (type of function,
    # in this case, rectifier (relu) and sigmoid (s shaped)
    model.add(Dense(2303, input_dim=inputDim, init='normal', activation='relu'))
    model.add(Dense(4608, init='normal', activation='relu'))
    model.add(Dense(4608, init='normal', activation='relu'))
    model.add(Dense(outputDim, init='normal', activation='sigmoid'))


    #this python is an interface to the theano or TensorFlow "backend"... this
    #thing that really runs. It automatically knows how to optimize itself for
    #your hardware.
    #must specify loss function like "binary_crossentropy" for binary output,
    #or efficient gradient descent algorithm "adam".
    #Finally, because it is a classification problem, we will collect and
    #report the classification accuracy as the metric.
    optim=keras.optimizers.Adagrad(lr=0.01, epsilon=1e-08)
    # Compile model
    #optim = keras.optimizers.SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(optimizer=optim, loss='mean_squared_error')

    #now we use our compiled model by running the fit() function. We specify:
    #number of interations (or epochs using nb_epoch)
    #set number of itertaions that happen before adjusting the weights (batch_size)
    
    model.fit(X,Y, nb_epoch=30, batch_size=1)


    '''
    #testSet = numpy.loadtxt("/work/chartd/users/daveotte/cpp/raytracer/render_data.txt", delimiter=",")
    #X = testSet[:,0:9]
    dataset = numpy.loadtxt("/work/rd/users/daveotte/machine_learning/raytracer/v4/test_data/test_data.txt", delimiter=",")
    # split into input (X) and output (Y) variables
    X = dataset[:,0:2]


    ## evaluate the model
    scores = model.predict_on_batch(X)
    #print scores
    x=0
    z=0
    y=0
    imageDir = "/work/rd/users/daveotte/machine_learning/raytracer/v4/test_result/"
    pixelOffset = 1
    width=96

    for i in scores:
        z = z+1
        print "score: " + str(z)
        for j in i:
    #        print  "j: " + str(y) + " " + str(j)
            imageFile = imageDir + "result." + str(y) + ".ppm"
            y=y+1
            f = open(imageFile, 'w')
            f.write("P3\n32 24\n255\n\n")
            for rgb in numpy.nditer(j):
                x=x+1
                f.write( str(int(rgb*255*pixelOffset)) + " " )
                #row
                if x%width==0:
                    f.write ("\n")
            f.write ("\n\n")
            f.close()
            x=0
        

    '''
    sys.exit(0)




initializeNN()

