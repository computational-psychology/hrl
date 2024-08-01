# Deploying your code in tha lab setup

- ensure the lab has installed the necessary libraries.
 consult installation, section xx for instructions
 
- change HRL call parameters

To run in your local machine, you use `graphics="gpu"` and `inputs="keyboard`,
which are the default values.
To run the same experiment in the lab, you need to change to
`graphics="datapixx"` (for the Datapixx 1 device) or 
`graphics="viewpixx"` (for the Viewpixx 3D device).
To use the response board, you need to change to `inputs="responsepixx"`.


- ensure you have a calibration file, so you pass a `lut.csv`. 
See section .. for instructions on how to do it.



