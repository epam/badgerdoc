**BadgerDoc** is a ML Delivery Platform made to make delivery process of Machine Learning Solutions visible to customer,
managers and ML team. The primary goal of the platform is to visualize ML model delivery cycle -  data annotation, 
model training and result visualization.

The platform has rich functionality in access and data management, annotation setups, and pipeline composition.
Access management is based on Keycloak, which is integrated with EPAM Active Directory.
Data can be uploaded in batches, organized into datasets as well as uploaded as a single file.
ML pipeline can be applied to a dataset, which will trigger batch processing, or to a single document.
BadgerDoc is capable of annotating large datasets by many annotators. It has algorithms for task distribution,
validation roles, several validation setups and will have multicoverage of files by annotators in nearest future.

BadgerDoc also has steady growing number of pre-trained models available for users, which can be assembled into pipelines through visual editor. 

Having such a rich functionality, BadgerDoc can be used for implementing full ML development cycle,
as well as for rapid prototyping, demonstrating EPAM expertise in ML and even for large annotation
project when preliminary annoation is available. 

For now, BadgerDoc is working with vectorized and scanned documents, but it has capability of image annotation.
