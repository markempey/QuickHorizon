# QuickHorizon
Description: calculates horizon elevation and azimuth from fisheye images

How to Use:
Import a fisheye image 
draw azimuth wheel 
fit azimuth wheel to fisheye image
draw field azimuth line ( must use a reference azimuth taken in the field)
Set the field azimuth value by using info displyed in the log ( change field az value until log displays the desired reference azimuth)
draw dots along horizon lines
export dot info to CSV file with coordinates, elevation ad azimuth 


Bugs:

-Field azimuth is set to -1 initially, it must be et to a value from 0-360 in order to be visible
-Rounds dot coordinates when in large zoom extent (they APPEAR shifted, ignore this)
-Must have field azimuth and azimuth wheel set inorder to export dot information
