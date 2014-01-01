import arcpy, math
from arcpy import mapping
import pythonaddins

class PointSelector(object):
    """Implementation for BoundaryAdjustAddIn_addin.BoundaryAdjuster (Tool)"""
    startPoint = None
    endPoint = None
    clickedStart = None
    clickedEnd = None
    
    def __init__(self):
        self.enabled = True
        self.shape = "NONE" # Can set to "Line", "Circle" or "Rectangle" for interactive shape drawing and to activate the onLine/Polygon/Circle event sinks.
        self.cursor = 3
        
        self.clickedStart = False
        self.clickedEnd = False
        
    def onMouseDown(self, x, y, button, shift):
        pass
    def onMouseDownMap(self, x, y, button, shift):
        pass
    def onMouseUp(self, x, y, button, shift):
        pass
    def onMouseUpMap(self, x, y, button, shift):
        if self.clickedStart == False:
            self.startPoint = arcpy.Point(x, y)
            self.clickedStart = True 
            print "Start point added: {}, {}".format(self.startPoint.X, self.startPoint.Y)
        elif self.clickedStart == True:
            self.endPoint = arcpy.Point(x, y)
            self.clickedEnd = True
            print "End point added: {}, {}".format(self.endPoint.X, self.endPoint.Y)
         
        print "Road is populated: {}".format(StartBoundaryAdjustButton.road != None)
        print "Clicked end point: {}".format(self.clickedEnd == True)
        if (StartBoundaryAdjustButton.road != None) and (self.clickedEnd == True):
            print "Begin CheckRoad."
            adjustmentRoad = StartBoundaryAdjustButton.road
            adjustPoints = CheckRoad(self.startPoint, self.endPoint, adjustmentRoad).getAdjustPoints()
            
            for point in adjustPoints:
                print "{}, {}".format(point.X, point.Y)
            
            print "Begin Boundary."
            roadSpatialRef = arcpy.Describe(StartBoundaryAdjustButton.boundary).spatialReference       
            with arcpy.da.UpdateCursor(StartBoundaryAdjustButton.boundary, "SHAPE@") as Cursor:
                for row in Cursor:
                    boundary = Boundary(adjustPoints, row[0])
                    adjustedBoundary = boundary.getUpdatedBoundary(roadSpatialRef)
                    row[0] = adjustedBoundary   
                    Cursor.updateRow(row) 
                    
            arcpy.RefreshActiveView()
            self.resetState()
            
    def onMouseMove(self, x, y, button, shift):
        pass
    def onMouseMoveMap(self, x, y, button, shift):
        pass
    def onDblClick(self):
        pass
    def onKeyDown(self, keycode, shift):
        pass
    def onKeyUp(self, keycode, shift):
        pass
    def deactivate(self):
        pass
    def onCircle(self, circle_geometry):
        pass
    def onLine(self, line_geometry):
        pass
    def onRectangle(self, rectangle_geometry):
        pass
    
    def resetState(self):
        StartBoundaryAdjustButton.road = None
        StartBoundaryAdjustButton.boundary = None
        self.clickedEnd = False
        self.clickedStart = False
        self.startPoint = None
        self.endPoint = None
        
class StartBoundaryAdjuster(object):
    """Implementation for BoundaryAdjustAddIn_addin.StartBoundaryAdjustButton (Button)"""
    #road = None
    
    def __init__(self):
        self.enabled = True
        self.checked = False
        self.road = None
        self.boundary = None
    def onClick(self):
        mxd = arcpy.mapping.MapDocument("CURRENT")
        layerList = mapping.ListLayers(mxd)
        
        with arcpy.da.UpdateCursor(layerList[0], 'FULLNAME') as cursor:
            for row in cursor:
                row[0] = "make it up?"
                cursor.updateRow(row) 
        
        self.road = layerList[0]
        self.boundary = layerList[1]
        print int(arcpy.GetCount_management(layerList[0]).getOutput(0))
        print layerList[0].name
        BoundaryAdjuster.enabled = True
        
        
class CheckRoad(object):
    
    _usrStartPnt = None
    _usrEndPnt = None
    _inputRoad = None
    _roadPoints = None
    adjustPoints = None
    
    def __init__(self, userStart, userEnd, userInputRoad):
        self._usrStartPnt = userStart
        self._usrEndPnt = userEnd
        self._inputRoad = userInputRoad
        self._roadPoints = self.getRoadPoints()
        self.adjustPoints = arcpy.Array()
        self._addAdjustPoints()
        
    def _distanceFormula(self, x1 , y1, x2, y2):
        d = math.sqrt((math.pow((x2 - x1),2) + math.pow((y2 - y1),2)))
        return d
    
    def _getRoadStartAndEndIndex(self):
        '''Takes the user-selected start and end points, finds the closest road points 
        to those start and end points, and returns their array indices in the form of a list.'''
        bufferDistance = 100
        
        minstartDist = None
        startPntIndex = -1
        foundZeroDistStartPnt = False
        
        minEndDist = None
        endPntIndex = -1
        foundZeroDistEndPnt = False
        
        i = 0;
        for point in self._roadPoints:
            startDist = self._distanceFormula(self._usrStartPnt.X, self._usrStartPnt.Y, point.X, point.Y)
            endDist = self._distanceFormula(self._usrEndPnt.X, self._usrEndPnt.Y, point.X, point.Y)
            
            #small rounding decimals make this useless right now
            if foundZeroDistStartPnt and foundZeroDistEndPnt:
                break
            
            #Select the point closest to the start point that is within the buffer
            if foundZeroDistStartPnt:
                foundZeroDistStartPnt = True
            elif minstartDist == None:
                minstartDist = startDist
                startPntIndex = i              
            elif startDist <= 0.009:
                minstartDist = startDist
                startPntIndex = i
                foundZeroDistStartPnt = True                                          
            elif startDist <= bufferDistance and startDist < minstartDist:
                minstartDist = startDist
                startPntIndex = i
            
            #Select the point closest to the end point that is within the buffer
            if foundZeroDistEndPnt:
                foundZeroDistEndPnt = True
            elif minEndDist == None:
                minEndDist = endDist
                endPntIndex = i              
            elif endDist <= 0.009:
                minEndDist = endDist
                endPntIndex = i 
                foundZeroDistEndPnt = True                                          
            elif endDist <= bufferDistance and endDist < minEndDist:
                minEndDist = endDist
                endPntIndex = i
            
            i += 1
            #print i                    
        
        if startPntIndex > endPntIndex:
            # switch indexes
            temp2 = startPntIndex
            startPntIndex = endPntIndex
            endPntIndex = temp2
            
        return [startPntIndex, endPntIndex]
    
    def _addAdjustPoints(self):
        '''Adds the road points between and including the start and 
        end point to the adjustPoints array.'''
        roadStartEnd = self._getRoadStartAndEndIndex()
        tempArray = range(roadStartEnd[0], roadStartEnd[1] + 1)
        for index in tempArray:
            self.adjustPoints.add(self._roadPoints[index])
        
    def getAdjustPoints(self):
        return self.adjustPoints
    
    def getRoadPoints(self):
        '''Returns an arcpy.Array of road points.'''
        # self._roadPoints = []
        with arcpy.da.SearchCursor(self._inputRoad, "SHAPE@") as Cursor:
            for row in Cursor:
                return row[0].getPart(0)
            
class Boundary(object):
    
    _adjustPoints = None
    _boundaryGeometry = None
    _boundaryPoints = None
    
    def __init__(self, adjustPoints, boundaryGeometry):
        self._adjustPoints = adjustPoints
        self._boundaryGeometry = boundaryGeometry
        self._boundaryPoints = self._getBoundaryArray()
        
    def _getBoundaryArray(self):
        return self._boundaryGeometry.getPart(0)
    
    def _findStartAndEndIndex(self):
        '''Finds the closest boundary points to the start and end road points. 
        Booleans replaceStart and replaceEnd determine whether the start and end boundary points should 
        be replaced with the start and end road points based on their proximity to each other.
        Returns a list containing: start index, end index, replaceStart?, replaceEnd?'''
        startIndex = None
        endIndex = None
        startDist = None
        endDist = None
        replaceStart = False
        replaceEnd = False
        startAdjustPoint = self._adjustPoints[0]
        endAdjustPoint = self._adjustPoints[self._adjustPoints.count - 1]
        bufferDistance = 500
        i = 0
        
        for point in self._boundaryPoints:
            tempStartDist = self._distanceFormula(point.X, point.Y, startAdjustPoint.X, startAdjustPoint.Y)
            tempEndDist = self._distanceFormula(point.X, point.Y, endAdjustPoint.X, endAdjustPoint.Y)
            
            if i == 0:
                startDist = tempStartDist
                startIndex = i
                endDist = tempEndDist
                endIndex = i
            else:
                if tempStartDist < startDist:
                    startDist = tempStartDist
                    startIndex = i

                if tempEndDist < endDist:
                    endDist = tempEndDist
                    endIndex = i
                    
            i += 1
            
        if startIndex > endIndex:
            temp = startIndex
            startIndex = endIndex
            endIndex = temp
            self._flipAdjustPoints()
            
        if startDist < bufferDistance:
            replaceStart = True
        if endDist < bufferDistance:
            replaceEnd = True
            
        return [startIndex, endIndex, replaceStart, replaceEnd]
    
    def _flipAdjustPoints(self):
        temp = arcpy.Array()
        for point in self._adjustPoints:
            temp.insert(0, point)
        self._adjustPoints = temp
    
    def _replaceBoundaryPoints(self):
        '''Replaces points in _boundaryPoints with _adjustPoints.'''
        startEndIndices = self._findStartAndEndIndex() 
        insertIndex = startEndIndices[0]
        startRemove = startEndIndices[0]
        endRemove = startEndIndices[1]
        discardedPoints = arcpy.Array()
        
        # Replace start point
        if startEndIndices[2]:
            self._boundaryPoints.replace(startEndIndices[0], self._adjustPoints[0])
            self._adjustPoints.remove(0)
            startRemove = startRemove + 1
            print "Replaced start point."
            insertIndex = insertIndex + 1
        # Replace end point
        if startEndIndices[3]:
            self._boundaryPoints.replace(startEndIndices[1], self._adjustPoints[self._adjustPoints.count - 1])
            self._adjustPoints.remove(self._adjustPoints.count - 1)
            print "Replaced end point."
            endRemove = endRemove - 1
            
        # Remove all points between start and end indices
        removeNum = endRemove - startRemove + 1
        for x in range(removeNum):
            discardedPoints.add(self._boundaryPoints[startRemove])
            self._boundaryPoints.remove(startRemove)
         
        # Insert new points    
        for point in self._adjustPoints:
            self._boundaryPoints.insert(insertIndex, point)
            insertIndex += 1
        #for pnt in discardedPoints:
            #print "{}, {}".format(pnt.X, pnt.Y)
            
        return discardedPoints
    
    def getUpdatedBoundary(self, bndSpatialReference):
        '''Returns updated boundary as a geometry object.'''
        self._replaceBoundaryPoints()
        tempBoundaryGeometry = arcpy.Polygon(self._boundaryPoints, bndSpatialReference)
        return tempBoundaryGeometry
    
    def _distanceFormula(self, x1 , y1, x2, y2):
        d = math.sqrt((math.pow((x2 - x1),2) + math.pow((y2 - y1),2)))
        return d
        