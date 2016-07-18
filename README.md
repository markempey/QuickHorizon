# QuickHorizon
Description: calculates horizon elevation and azimuth from fisheye images

How to Use:
1)Import a fisheye image ("file", "open image") 
2)Draw azimuth wheel ("azimuth", "show azimuth wheel")
3)Fit azimuth wheel to fisheye image using x,y corrds of centre and radius 
4)Find field azimuth (must use a reference object from the field)
-first click on reference object
-hold mouse buttom and slide the green line until the field azimuth dialog (bottom left of GUI) reads the azimuth determined in the field
-release mouse to set field azimuth
5)Digitize dots along the apparent horizon in the image ("Tools", "Digitize")
6)Export to CSV file with image pixel coordinates, elevation and azimuth ("file", "export csv")


Extra:
-Rounds dot coordinates when in large zoom extent (they APPEAR shifted, ignore this)
-can delete dots 
