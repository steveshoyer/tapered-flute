# Program to create g-code to cut a tapered flute
# The flute is cut in line with the X axis
#
# WARNING: THIS PROGRAM GENERATES G CODE THAT MIGHT NOT WORK FOR YOUR APPLICATION.  IT IS THE USER'S RESPONSIBILITY
# TO TEST THE G CODE.  THE AUTHOR WILL NOT BE RESPONSIBLE FOR DAMAGE AND/OR INJURY CAUSED BY THE USE OF THIS PROGRAM.
# USE OF A SIMULATOR IS STRONGLY SUGGESTED BEFORE RUNNING ON A LIVE CNC MACHINE.  SERIOUSLY.
#
# Author: Steve Shoyer
# Version: 1
# Date: Feb 1 2016
#
# Released under the MIT License rules - see LICENSE file for details
#
# Dimensions are in inches, although the calculations should work for metric dimensions as well (not tested)
#
# Basically, this program breaks up the width of a tapered flute into multiple steps along the X axis.  For each step, the appropriate
# Z height of the cutter is determined using a formula to find a single point tangent to two circles.  The larger circle
# has a center at X1,Z1 and a radius of R1, and the inner/smaller circle has a center at X2,Z2 and a radius of R2.  The
# formula is ((X1-X2)^2) + (Z1-Z2)^2) = (R1-R2)^2 (see http://mathworld.wolfram.com/TangentCircles.html for more info).
# So, we vary the X2 value, and solve the equation for the corresponding Z2
#
# The toolpath is not optimized.  Each pass starts at the far end of the flute and cuts down one side, then returns to the top
# of the flute to cut the other side of the center line.  It cuts a lot of air as well, because each cut starts above the 
# playfield and descends into it on a sloping line.  Also, I wanted to only use downward cuts for the taper in the hopes that a
# downward cut would be smoother than an upward one, so the cutter is repositioned after each pass.
#
# Instructions:
#
# 1) set variables in the "input values" section to correspond to your cutter and playfield
# 2) look through the "start the file with g-code" section to see if it will work for your machine, make changes as needed
# 3) run the program
# 4) copy the output from the program into a text file
# 5) look at the file - remove the "Remove this line" line in the beginning
# 6) test the output in a CNC simulator to verify that it is doing what you want it to do
# 7) use the g code to cut your shooter lane tapered flute
#

import math

# input values 
x_center = 5 # X coordinate of centerline of flute
y_start = 10 #  Y starting coordinate, 0% depth of cut
y_end = 0  # Y ending coordinate, 100% depth of cut
depth = 0.25  # depth of cut
flute_radius = 0.53125 # radius of flute to be cut, 1-1/16" dia
tool_radius = 0.125 # radius of cutter, a .25" ball end mill
stepover_pct = 33  # percentage of stepover for each cut; valid range is 1-100
spindle_rpm = 12000  # spindle rotation rate
feedrate = 60.0  # feedrate, in inches per minute

# calculated values 
min_num_cuts = flute_radius  // tool_radius   # half of the minimum number of cuts to clear the flute
num_cuts = min_num_cuts * (100 // stepover_pct)  # larger stepover makes for a smoother end result, but takes more time
x_change_per_step = (flute_radius - tool_radius) / num_cuts  # the cut starts one tool radius in and ends one tool radius in, so the outer edge of the cutter is at the outer edge of the flute

# start the file with g-code for a typical Mach3 job - change this if not using Mach3, possibly not all needed for this job
print('%')  # start the file
print('Remove this line after verifying the operation of this program') # annoying line to remind the user to test the code
print('G00G20G17G90G40G49G80') # G20=programming in inches;G17=XY plane;G90=absolute positioning;G40=tool radius compensation off;G49=tool length offset compensation off;G80=cancel canned cycle
print('G70G91.1') # G70=Fixed cycle, multiple repetitive cycle, for finishing;G91.1=incremental IJK mode
print('T1M06') # T1M06=tool 1 for ATC
print('(Ball End Mill {{{0} inch}})'.format(tool_radius*2))
print('G00G43Z{0}10H1'.format(tool_radius*2))
print('S{0}M03'.format(spindle_rpm)) # spindle on, clockwise
print('(Toolpath:- Profile)')
print('()')
print('G94') # feedrate, inches per minute
print('X0.0000Y0.0000F{0}'.format(feedrate)) # feedrate for G01 moves

print('G0 Z0.1  (move to a point above the workpiece)')

# initialize loop 
current_step = 0
x_one = x_center  # the X-coordinate of the larger circle's center is an input value
z_one = flute_radius  # the Z coordinate of the larger circle's center is equal to the flute radius, so the cut starts at Z=0
r_one = flute_radius  # the radius of the larger circle is an input value, the flute's radius
r_two = tool_radius  # the radius of the smaller circle is the radius of the cutting tool, a ball nose cutter

while (current_step <= num_cuts):
    # start from the outsides of the flute and move in for each pass
    x_left = x_one - flute_radius + tool_radius + (current_step * x_change_per_step)  # set the X coordinate on the left side of the cut
    x_right = x_one + flute_radius - tool_radius - (current_step * x_change_per_step)  # set the X coordinate for the right side of the cut
    # solving Z2 = Z1 - sqrt((R1-R2+X1-X2)*(R1-R2-X1+X2)) - because the cut is mirrored on both sides of the center line, 
    # Z2 is the same distance for x_left and x_right
    z_two = z_one - math.sqrt((r_one - r_two + x_one - x_left) * (r_one - r_two - x_one + x_left))
    z_two_start = z_two - tool_radius  # Z2 is the center of the cutter radius, so we need to find the bottom of the cutter
    z_two_end = z_two_start - depth  # add the depth of the cut to get the ending Z height
    print('( Step: {0} )'.format(current_step))
    print('G0 X{0} Y{1} Z{2}'.format(x_right,y_start,z_two_start))
    print('G1 Y{0} Z{1}'.format(y_end,z_two_end))
    print('G0 Z0.1') # safe Z
    if (x_left <> x_right):  # no need to cut the same path twice
        print('G0 X{0} Y{1} Z{2}'.format(x_left,y_start,z_two_start))
        print('G1 Y{0} Z{1}'.format(y_end,z_two_end))
        print('G0 Z0.1') # safe Z
    current_step = current_step + 1
    

print('G0 X0 Y0 Z0.1  ( return to home )')
print('M09  ( turn off coolant)')
print('M30  ( end of program )')

print('%') # end of g-code file
