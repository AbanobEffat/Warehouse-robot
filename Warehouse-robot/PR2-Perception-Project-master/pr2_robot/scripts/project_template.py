#!/usr/bin/env python

# Import modules
import numpy as np
import sklearn
from sklearn.preprocessing import LabelEncoder
import pickle
from sensor_stick.srv import GetNormals
from sensor_stick.features import compute_color_histograms
from sensor_stick.features import compute_normal_histograms
from visualization_msgs.msg import Marker
from sensor_stick.marker_tools import *
from sensor_stick.msg import DetectedObjectsArray
from sensor_stick.msg import DetectedObject
from sensor_stick.pcl_helper import *

import rospy
import tf
from geometry_msgs.msg import Pose
from std_msgs.msg import Float64
from std_msgs.msg import Int32
from std_msgs.msg import String
from pr2_robot.srv import *
from rospy_message_converter import message_converter
import yaml


# Helper function to get surface normals
def get_normals(cloud):
    get_normals_prox = rospy.ServiceProxy('/feature_extractor/get_normals', GetNormals)
    return get_normals_prox(cloud).cluster

# Helper function to create a yaml friendly dictionary from ROS messages
def make_yaml_dict(test_scene_num, arm_name, object_name, pick_pose, place_pose):
    yaml_dict = {}
    yaml_dict["test_scene_num"] = test_scene_num.data
    yaml_dict["arm_name"]  = arm_name.data
    yaml_dict["object_name"] = object_name.data
    yaml_dict["pick_pose"] = message_converter.convert_ros_message_to_dictionary(pick_pose)
    yaml_dict["place_pose"] = message_converter.convert_ros_message_to_dictionary(place_pose)
    return yaml_dict

# Helper function to output to yaml file
def send_to_yaml(yaml_filename, dict_list):
    data_dict = {"object_list": dict_list}
    with open(yaml_filename, 'w') as outfile:
        yaml.dump(data_dict, outfile, default_flow_style=False)

# Callback function for your Point Cloud Subscriber
def pcl_callback(pcl_msg):

    # Convert ROS msg to PCL data
    cloud = ros_to_pcl(pcl_msg)

    # Since the raw Point Cloud contains unnecessary data making publishing intensive, its a good idea to trim it first.
    # PassThrough Filters
    passthrough = cloud.make_passthrough_filter()
    passthrough.set_filter_field_name('y')
    passthrough.set_filter_limits(-0.5, 0.5)
    cloud_passthrough = passthrough.filter()

    passthrough = cloud_passthrough.make_passthrough_filter() 
    passthrough.set_filter_field_name('z')
    passthrough.set_filter_limits(0.6, 1.2)
    cloud_passthrough = passthrough.filter()

    # Statistical Outlier Filtering
    stats = cloud_passthrough.make_statistical_outlier_filter()
    stats.set_mean_k(1)    
    stats.set_std_dev_mul_thresh(1.0)
    cloud_stats = stats.filter()

    # Voxel Grid Downsampling
    vox = cloud_stats.make_voxel_grid_filter()
    LEAF_SIZE = 0.01
    vox.set_leaf_size(LEAF_SIZE, LEAF_SIZE, LEAF_SIZE)
    cloud_vox = vox.filter()

    # RANSAC Plane Segmentation
    seg = cloud_vox.make_segmenter()
    seg.set_model_type(pcl.SACMODEL_PLANE)
    seg.set_method_type(pcl.SAC_RANSAC)
    max_distance = 0.01
    seg.set_distance_threshold(max_distance)
    inliers, coefficients = seg.segment()

    # Extract inliers and outliers
    cloud_table = cloud_vox.extract(inliers, negative=False)
    cloud_objects = cloud_vox.extract(inliers, negative=True)
    

    # Euclidean Clustering
    white_cloud = XYZRGB_to_XYZ(cloud_objects)
    tree = white_cloud.make_kdtree()
    
    ec = white_cloud.make_EuclideanClusterExtraction()
    ec.set_ClusterTolerance(0.05)
    ec.set_MinClusterSize(50)
    ec.set_MaxClusterSize(2500)
    ec.set_SearchMethod(tree)

    # cluster_indices contains a list of indices for each cluster (a list of list)
    cluster_indices = ec.Extract()

    # Create Cluster-Mask Point Cloud to visualize each cluster separately
    cluster_color = get_color_list(len(cluster_indices))

    color_cluster_point_list = []

    for j, indices in enumerate(cluster_indices):
        for i, indice in enumerate(indices):
            color_cluster_point_list.append([white_cloud[indice][0],
                                            white_cloud[indice][1],
                                            white_cloud[indice][2],
                                            rgb_to_float(cluster_color[j])])

    cloud_cluster = pcl.PointCloud_PointXYZRGB()
    cloud_cluster.from_list(color_cluster_point_list)    


    # Convert PCL data to ROS messages
    ros_cloud_passthrough = pcl_to_ros(cloud_passthrough)
    ros_cloud_stats = pcl_to_ros(cloud_stats)
    ros_cloud_vox = pcl_to_ros(cloud_vox)
    ros_cloud_table = pcl_to_ros(cloud_table)
    ros_cloud_objects = pcl_to_ros(cloud_objects)
    ros_cloud_cluster = pcl_to_ros(cloud_cluster)

    # Publish ROS messages
    pcl_pub_passthrough.publish(ros_cloud_passthrough)
    pcl_pub_stats.publish(ros_cloud_stats)
    pcl_pub_vox.publish(ros_cloud_vox)
    pcl_pub_table.publish(ros_cloud_table)
    pcl_pub_objects.publish(ros_cloud_objects)    
    pcl_pub_cluster.publish(ros_cloud_cluster)

    detected_objects_labels = []
    detected_objects = []

    # Classify the clusters! (loop through each detected cluster one at a time)
    for index, pts_list in enumerate(cluster_indices):
        # Grab the points for the cluster
        pcl_cluster = cloud_objects.extract(pts_list)
        ros_cluster = pcl_to_ros(pcl_cluster)

        # Compute the associated feature vector
        chists = compute_color_histograms(ros_cluster, using_hsv=True)
        normals = get_normals(ros_cluster)
        nhists = compute_normal_histograms(normals)
        feature = np.concatenate((chists, nhists))

        # Make the prediction
        prediction = clf.predict(scaler.transform(feature.reshape(1,-1)))
        label = encoder.inverse_transform(prediction)[0]
        detected_objects_labels.append(label)

        # Publish a label into RViz
        label_pos = list(white_cloud[pts_list[0]])
        label_pos[2] += .4
        object_markers_pub.publish(make_label(label, label_pos, index))

        # Add the detected object to the list of detected objects.
        do = DetectedObject()
        do.label = label
        do.cloud = ros_cluster
        detected_objects.append(do)

    rospy.loginfo('Detected {} objects: {}'.format(len(detected_objects_labels), detected_objects_labels))

    # Publish the list of detected objects
    detected_objects_pub.publish(detected_objects)

    # Suggested location for where to invoke your pr2_mover() function within pcl_callback()
    # Could add some logic to determine whether or not your object detections are robust
    # before calling pr2_mover()
    
    try:
        pr2_mover(detected_objects)
    except rospy.ROSInterruptException:
        pass
    

# function to load parameters and request PickPlace service
def pr2_mover(object_list):
    
    # Initialize variables
    test_scene_num = Int32()
    object_name = String()    
    object_group = String()
    arm_name = String()
    pick_pose = Pose()
    place_pose = Pose()

    test_scene_num.data = 2    
   
    # Get/Read parameters
    object_list_param = rospy.get_param('/object_list')
    dropbox_list_param = rospy.get_param('/dropbox')

    # TODO: Rotate PR2 in place to capture side tables for the collision map
    
    dict_list = []
    # Loop through the pick list
    for object in object_list:

        # Get the PointCloud for a given object and obtain it's centroid
        object_name.data = str(object.label)        
        points_arr = ros_to_pcl(object.cloud).to_array()
        centroid = np.mean(points_arr, axis=0)[:3]   

        # Assign the arm to be used for pick_place
        for i in range(0, len(object_list_param)):
            # Parse parameters into individual variables
            if object_name.data == object_list_param[i]['name']:
                object_group.data = object_list_param[i]['group']

        if object_group.data == 'green':
            arm_name.data = 'right'
        else:
            arm_name.data = 'left'

        # Create 'pick_pose' for the object
        pick_pose.position.x = np.asscalar(centroid[0])
        pick_pose.position.y = np.asscalar(centroid[1])
        pick_pose.position.z = np.asscalar(centroid[2])    

        # Create 'place_pose' for the object
        for i in range(0, len(dropbox_list_param)):
            if object_group.data == dropbox_list_param[i]['group']:
                dropbox = dropbox_list_param[i]['position']

        place_pose.position.x = np.float(dropbox[0])
        place_pose.position.y = np.float(dropbox[1])
        place_pose.position.z = np.float(dropbox[2])

        # Create a list of dictionaries (made with make_yaml_dict()) for later output to yaml format
        yaml_dict = make_yaml_dict(test_scene_num, arm_name, object_name, pick_pose, place_pose)
        dict_list.append(yaml_dict)

        # Wait for 'pick_place_routine' service to come up
        rospy.wait_for_service('pick_place_routine')

        try:
            pick_place_routine = rospy.ServiceProxy('pick_place_routine', PickPlace)

            # Insert your message variables to be sent as a service request
            resp = pick_place_routine(test_scene_num, object_name, arm_name, pick_pose, place_pose)

            print ("Response: ",resp.success)

        except rospy.ServiceException, e:
            print "Service call failed: %s"%e

    # Output your request parameters into output yaml file
    send_to_yaml('output_3.yaml', dict_list)


if __name__ == '__main__':

    # ROS node initialization
    rospy.init_node('clustering', anonymous=True)

    # Create Subscribers
    pcl_sub = rospy.Subscriber("/pr2/world/points", pc2.PointCloud2, pcl_callback, queue_size=1)

    # Create Publishers
    pcl_pub_passthrough = rospy.Publisher("/pcl_passthrough", PointCloud2, queue_size=1)
    pcl_pub_stats = rospy.Publisher("/pcl_stats", PointCloud2, queue_size=1)
    pcl_pub_vox = rospy.Publisher("/pcl_vox", PointCloud2, queue_size=1)
    pcl_pub_table = rospy.Publisher("/pcl_table", PointCloud2, queue_size=1)
    pcl_pub_objects = rospy.Publisher("/pcl_objects", PointCloud2, queue_size=1)
    pcl_pub_cluster = rospy.Publisher("pcl_cluster", PointCloud2, queue_size=1)   
    object_markers_pub = rospy.Publisher("/object_markers", Marker, queue_size=1)
    detected_objects_pub = rospy.Publisher("/detected_objects", DetectedObjectsArray, queue_size=1) 

    # Load Model From disk
    model = pickle.load(open('model2.sav', 'rb'))
    clf = model['classifier']
    encoder = LabelEncoder()
    encoder.classes_ = model['classes']
    scaler = model['scaler']

    # Initialize color_list
    get_color_list.color_list = []

    # Spin while node is not shutdown
    while not rospy.is_shutdown():
        rospy.spin()

