# Qt Pitch Overlay
>  [!CAUTION] 
> This project is currently a gigantic WIP. Documentation is non-existent, if you build this using PyInstaller, the 
> resulting files are enormous (that's what bundling TensorFlow as a dependency gets you).

## Technical information
Pitch estimation is somewhat complicated to solve using algorithmic methods.
This project uses [CREPE](https://github.com/marl/crepe), a neural network based pitch estimator.