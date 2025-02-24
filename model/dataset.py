import os
import glob
import numpy as np
import cv2
import imageio
import sklearn.utils
import logging
from tqdm import tqdm
#from model.tfhelper import show_progress


# Source inspired from CV-Tricks.com and https://github.com/sankit1/cv-tricks.com/blob/master/Tensorflow-tutorials/tutorial-2-image-classifier/dataset.py


def load_train(train_path, image_size, classes):
    """
    Load the training test data set from the path give by assuming:
    # assuming data directory has a separate folder for each class, and that each folder is named after the class
    1) the class label is the folder name.
    2) files end with 'g' such as png, jpg, etc. No CAPITAL.
    3) image can be linearly downsized to image_size x image_size
    :param train_path:
    :param image_size:
    :param classes:
    :return:
    """

    logger = logging.getLogger("Loading Training Dataset from: " + train_path)
    # Initialize the arrays null.
    images = [] # numpy image raw array data.
    labels = [] # labe of the image, in an array of LEN (0 to class)
    ids = [] # actual file name of the image
    cls = [] # actual class label in string.



    # Traverse every single class of images.
    for current_class in classes:

        # Find class_index of the current class.
        class_index = classes.index(current_class)
        logger.info('Loading {} files (Index: {})'.format(current_class, class_index))

        # wild card for jpg, png?
        path = os.path.join(train_path, current_class, '*g')
        logger.info('Loading: ' + path)

        # List all files from a path.
        files_list = glob.glob(path)

        # Traverse all files of the particular class.
        for file_path in tqdm(files_list):

            # OpenCV IMREAD the file_path
            image = cv2.imread(file_path)
            # resize the image to the dimension given? (x=y?) using linear interprelator
            image = cv2.resize(image, (image_size, image_size), cv2.INTER_LINEAR)
            # add image to image LIST.
            images.append(image)

            # Establish a 0 to X label array, where X is the number of MAXIMUM possible classes.
            label = np.zeros(len(classes))
            # Set the current INDEX of the above array to 1. (vector of all zeros, indicate current class as 1)
            label[class_index] = 1.0
            # add to the label LIST
            labels.append(label)

            # Get folder.
            file_name = os.path.basename(file_path)

            # Append file to an ID list.
            ids.append(file_name)

            # Append folder (class name) to an list.
            cls.append(current_class)

    images = np.array(images)
    labels = np.array(labels)
    ids = np.array(ids)
    cls = np.array(cls)

    return images, labels, ids, cls


def load_test(test_path, image_size):
    """
    Load a sets of files from teh path and resize them appropriately.
    1. only jpg/png files.
    :param test_path:
    :param image_size: 
    :return:
    """
    # Build glob search string
    path = os.path.join(test_path, '*g')

    # sort output into files.
    files = sorted(glob.glob(path))

    # Initialize null lists
    X_test = []
    X_test_id = []

    logger = logging.getLogger("Loading test dataset from " + path)

    for file_path in tqdm(files):

        file_name = os.path.basename(file_path)

        # OpenCV read image.
        img = cv2.imread(file_path)
        # OpenCV resize iamge.
        img = cv2.resize(img, (image_size, image_size), cv2.INTER_LINEAR)

        # Append image to test image numpy list.
        X_test.append(img)

        # Append image to test image ID string list.
        X_test_id.append(file_name)

    ### because we're not creating a DataSet object for the test images, normalization happens here

    # Convert to uInt8 for raw image data.
    X_test = np.array(X_test, dtype=np.uint8)

    # Convert to uInt8 for Floast32?
    X_test = X_test.astype('float32')

    # Normalize it to 255, 8 bit?
    X_test = X_test / 255

    return X_test, X_test_id


class DataSet(object):
    """
    A class for storing the data for ease of handling.
    """

    def __init__(self, images, labels, ids, cls):
        """
        Constructor:Construct a DataSet. one_hot arg is used only if fake_data is true.
        :param images:
        :param labels:
        :param ids:
        :param cls:
        """

        self._num_examples = images.shape[0]

        # Convert shape from [num examples, rows, columns, depth]
        # to [num examples, rows*columns] (assuming depth == 1)
        # Convert from [0, 255] -> [0.0, 1.0].

        images = images.astype(np.float32)
        images = np.multiply(images, 1.0 / 255.0)

        self._images = images
        self._labels = labels
        self._ids = ids
        self._cls = cls
        self._epochs_completed = 0

        self._index_in_epoch = 0    # what is this?


    # Propery lists constructed.
    @property
    def images(self):
        return self._images
    @property
    def labels(self):
        return self._labels
    @property
    def ids(self):
        return self._ids
    @property
    def cls(self):
        return self._cls

    # Return N
    @property
    def num_examples(self):
        return self._num_examples

    # An indexer to keep track of the number of training epoch completed.
    @property
    def epochs_completed(self):
        return self._epochs_completed

    # An instance function
    def next_batch(self, batch_size):
        """
        Return the next `batch_size` examples from this data set, IF ran out of examples to draw from, quit and start a new batch.
        This function update and keep track of the how much of the epoch we have gone through
        :param batch_size:
        :return:
        """

        # Batch size needs to be smaller than the number of available examples ALWAYS
        if not batch_size <= self._num_examples:
            raise ValueError("Batch size MUST be smaller than the number of test examples available")

        start = None
        end = None

        last_end_point = self._index_in_epoch
        remaining_samples = self._num_examples - last_end_point

        # Based on epoch completion status, we see only the batch that are relevant given current epoch.

        # When, epoch is not finished, simply draw from the remaining:
        if batch_size <= remaining_samples:

            # Retrieve current epoch training example index
            start = self._index_in_epoch
            end = self._index_in_epoch + batch_size

            # Set the Index in epoch for subsequent batch
            self._index_in_epoch = self._index_in_epoch + batch_size

        # When epoch is finished, start a new epoch, get more data to train.
        elif batch_size > remaining_samples :

            # Increment epoch count by 1 as not enough examples left to train, consider the epoch Finished
            self._epochs_completed += 1

            # # Shuffle the data (maybe)
            # perm = np.arange(self._num_examples)
            # np.random.shuffle(perm)
            # self._images = self._images[perm]
            # self._labels = self._labels[perm]
            # Start next epoch

            # start from 0 index.

            # Training start from teh beginning, to the batch size.
            start = 0
            end = batch_size - 1

            # set the ending point properly so next batch starts properly from the epoch index.
            self._index_in_epoch = batch_size - 1

        # retun the dataset from which we extract this batch: from the start (0 or the left over from last point) to the designed the end poitn.
        return self._images[start:end], self._labels[start:end], self._ids[start:end], self._cls[start:end]

def read_train_sets(train_path, image_size, classes, validation_size=0):
    """
    Load the training dataset, separate them into validation portion OR not.
    :param train_path:
    :param image_size:
    :param classes:
    :param validation_size:
    :return: a initialized datasets that contain its own training portion and its validation porition
    """

    # Reference the class object
    class DataSets(object):
        pass

    # Instantiate the empty object.
    data_sets = DataSets()

    # load training data.
    images, labels, ids, cls = load_train(train_path, image_size, classes)

    # Shuttle training data list wise, disrupt order but kept the index across all of them congruent.
    images, labels, ids, cls = sklearn.utils.shuffle(images, labels, ids, cls)  # shuffle the data

    # Validation must be a float number. Usually less than 1. Kind of pointless to be more than 1.
    if isinstance(validation_size, float):

        # Get precise integer number of the images to be used as the validation set
        validation_size = int(validation_size * images.shape[0])

    # Establish validation set size as everything UP to that validation size from teh beginning.
    validation_images = images[:validation_size]
    validation_labels = labels[:validation_size]
    validation_ids = ids[:validation_size]
    validation_cls = cls[:validation_size]

    # Establish training set size as everything FROM validation size to the end of the raw data array.
    train_images = images[validation_size:]
    train_labels = labels[validation_size:]
    train_ids = ids[validation_size:]
    train_cls = cls[validation_size:]

    # Create a PROPERTY of the training subdataset using the subset of raw data based on the index delineation point.
    data_sets.train = DataSet(train_images, train_labels, train_ids, train_cls)

    # Create a PROPERTY of the validation subdataset using the subset of raw data based on the index delineation point.
    data_sets.valid = DataSet(validation_images, validation_labels, validation_ids, validation_cls)

    return data_sets


def read_test_set(test_path, image_size):
    """
    Read the test data set. Really just a wrapper for load_test.
    :param test_path:
    :param image_size:
    :return:
    """
    images, ids = load_test(test_path, image_size)
    return images, ids