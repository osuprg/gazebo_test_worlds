Be sure to include the models directory in you Gazebo models path
  - To do so, add "export GAZEBO_MODEL_PATH=~/[path to package]/models:$GAZEBO_MODEL_PATH" to your .bashrc
  - This will allow you to place model.sdf and model.config files in the models folder in this package.
  - Any properly formatted models in that folder can be imported with <include> <uri> models://[model name] </uri> </include>
  
Manual additions of model information are required for actors.
For static models:
  - Option 1: Use a URI to use a model from a different file
  - Option 2: Include all link information for the model in the actor tag
For animated models:
  - All information about the model must be included in the actor tag
