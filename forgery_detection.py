import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
import ast

from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.utils import Sequence
from tensorflow.keras.applications import MobileNet
from tensorflow.keras.models import Sequential,Model
from tensorflow.keras.layers import Dense,Dropout , Activation, Flatten, GlobalAveragePooling2D
from tensorflow.keras.layers import Conv2D , ZeroPadding2D ,MaxPooling2D
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import EarlyStopping , ReduceLROnPlateau
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

data=r'Datasets/Train'

size=32
h=224
w=224

train_data=ImageDataGenerator(zoom_range=0.15,width_shift_range=0.2,shear_range=0.15)
test_data=ImageDataGenerator()

train=train_data.flow_from_directory(data,target_size=(h,w),
                                     class_mode="categorical",batch_size=size,subset="training")
test=test_data.flow_from_directory(data,target_size=(h,w),
                                     class_mode="categorical",batch_size=size,shuffle=False)

classess=train.num_classes

Mobilenet=MobileNet(weights='imagenet',include_top=False,input_shape=(224,224,3))

for i in Mobilenet.layers:
    i.trainable=False

def main_model(t1_model, classess):
    m_model = t1_model.output
    m_model = GlobalAveragePooling2D()(m_model)
    m_model = Dense(1024, activation='relu')(m_model)
    m_model = Dense(1024, activation='relu')(m_model)
    m_model = Dense(512, activation='relu')(m_model)
    m_model = Dense(classess, activation='softmax')(m_model)
    return m_model


combining_model=main_model(Mobilenet,classess)

model=Model(inputs=Mobilenet.input , outputs=combining_model)

model.compile(optimizer="Adam",loss="categorical_crossentropy",metrics=["accuracy"])
model.summary()

earlystop=EarlyStopping(patience=10)
learning_rate_reduce=ReduceLROnPlateau(monitor='val_accuracy',min_lr=0.001)
callbacks=[earlystop,learning_rate_reduce]

history=model.fit(train,validation_data=test,epochs=5)

model.save('mobilent_project.h5')

test_score=model.evaluate(test)

target_names=[]
for key in train.class_indices:
    target_names.append(key)

def plot_confusion_matrix(cm,classes,normalize=False,title='Confusion matrix', cmap=plt.cm.Blues):
    plt.figure(figsize=(10,10))

    plt.imshow(cm,interpolation='nearest',cmap=cmap)
    plt.title(title)
    plt.colorbar()

    tick_marks=np.arrange(len(classes))
    plt.xticks(tick_marks,classes,rotation=45)
    plt.yticks(tick_marks,classes)

    if normalize:
        cm=cm.astype('float')/cm.sum(axis=1)[:,np.newaxis]
        cm=np.around(cm,decimals=2)
        cm[np.isnan(cm)]=0.0
        print("Normalized confusion matrix")
    else:
        print("Confusion matrix, without normalization")
    thresh=cm.max()/2.
    for i , j in itertools.product(range(cm.shape[0]),range(cm.shape[1])):
        plt.text(j,i,cm[i,j],horizontalalignment='center',color="white" if cm[i,j]>thresh else "black")
        plt.tight_layout()
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")

Y_pred=model.predict(test)
y_pred=np.argmax(Y_pred,axis=-1)
print("Confusion matrix")
cm=confusion_matrix(test.classes,y_pred)

plot_confusion_matrix(cm,target_names,title='Confusion Matrix')
print("Classification report")
print(classification_report(test.classes,y_pred,target_names=target_names))

train_accuracy=history.history['accuracy']
val_accuracy=history.history['val_accuracy']
train_loss=history.history['loss']
val_loss=history.history['val_loss']

epochs=range(len(train_accuracy))
plt.figure(figsize=(12,4))
plt.subplot(1,2,1)
plt.plot(epochs,train_accuracy,'b',label='Training accuracy')      
plt.plot(epochs,val_accuracy,'r',label='validation accuracy')       
plt.title("Training and validation accuracy")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend(["Train","Val"],loc="upper right")

plt.show()

labels=train.class_indices
final_labels={v:k for k, v in labels.items()}

def predict_image(imgname,from_test_dir):
    test_image=image.load_img(imgname,target_size=(224,224))
    plt.imshow(test_image)
    plt.show()
    test_image=np.asarray(test_image)
    test_image=np.expand_dims(test_image,axis=0)
    result=model.predict(test_image)

    result_dict=dict()

    for key in list(final_labels.keys()):
        result_dict[final_labels[key]]=result[0][key]
    sorted_results={k: v for k , v in sorted(result_dict.items(),key=lambda item:item[1], reverse=True)}
    
    if not from_test_dir:
        print('='*50)
        for label in sorted_results.keys():
            print("{}: {}%".format(label,sorted_results[label]*100))
    final_result=dict()
    final_result[list(sorted_results.keys())[0]]=sorted_results[list(sorted_results.keys())[0]]*100

    return final_result
final_result1= predict_image(r'Datasets\Test\6531.png',False)
print("Final result: ",final_result1)