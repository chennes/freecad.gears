# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

from __future__ import division
import FreeCAD as App
from _involute_tooth import involute_tooth, involute_rack
from _cycloide_tooth import cycloide_tooth
from _bevel_tooth import bevel_tooth
from Part import BSplineCurve, Shape, Wire, Face, makePolygon, \
    BRepOffsetAPI, Shell, makeLoft, Solid, Line, BSplineSurface
from numpy import pi, cos, sin, tan

import numpy


def fcvec(x):
    if len(x) == 2:
        return(App.Vector(x[0], x[1], 0))
    else:
        return(App.Vector(x[0], x[1], x[2]))


class involute_gear():

    """FreeCAD gear"""

    def __init__(self, obj):
        self.involute_tooth = involute_tooth()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyBool", "undercut", "gear_parameter", "undercut")
        obj.addProperty(
            "App::PropertyFloat", "shift", "gear_parameter", "shift")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyAngle", "alpha", "involute_parameter", "alpha")
        obj.addProperty(
            "App::PropertyFloat", "clearence", "gear_parameter", "clearence")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "gear_parameter", "number of points for spline")
        obj.addProperty(
            "App::PropertyAngle", "beta", "gear_parameter", "beta ")
        obj.addProperty(
            "App::PropertyLength", "backlash", "gear_parameter", "backlash in mm")
        obj.addProperty("App::PropertyPythonObject", "gear", "test", "test")
        obj.gear = self.involute_tooth
        obj.teeth = 15
        obj.module = '1. mm'
        obj.undercut = True
        obj.shift = 0.
        obj.alpha = '20. deg'
        obj.beta = '0. deg'
        obj.height = '5. mm'
        obj.clearence = 0.25
        obj.numpoints = 6
        obj.backlash = '0.00 mm'
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        fp.gear.m_n = fp.module.Value
        fp.gear.z = fp.teeth
        fp.gear.undercut = fp.undercut
        fp.gear.shift = fp.shift
        fp.gear.alpha = fp.alpha.Value * pi / 180.
        fp.gear.beta = fp.beta.Value * pi / 180
        fp.gear.clearence = fp.clearence
        fp.gear.backlash = fp.backlash.Value
        fp.gear._update()
        pts = fp.gear.points(num=fp.numpoints)
        wi = []
        for i in pts:
            out = BSplineCurve()
            out.interpolate(map(fcvec, i))
            wi.append(out)
        s = Wire(Shape(wi).Edges)
        wi = []
        for i in range(fp.gear.z):
            rot = App.Matrix()
            rot.rotateZ(-i * fp.gear.phipart)
            tooth_rot = s.transformGeometry(rot)
            if i != 0:
                pt_0 = wi[-1].Edges[-1].Vertexes[0].Point
                pt_1 = tooth_rot.Edges[0].Vertexes[-1].Point
                wi.append(Wire([Line(pt_0, pt_1).toShape()]))
            wi.append(tooth_rot)
        pt_0 = wi[-1].Edges[-1].Vertexes[0].Point
        pt_1 = wi[0].Edges[0].Vertexes[-1].Point
        wi.append(Wire([Line(pt_0, pt_1).toShape()]))

        wi = Wire(wi)
        fp.Shape = wi
        if fp.beta.Value == 0:
            sh = Face(wi)
            fp.Shape = sh.extrude(App.Vector(0, 0, fp.height.Value))
        else:
            fp.Shape = helicalextrusion(
                wi, fp.height.Value, fp.height.Value * tan(fp.gear.beta) * 2 / fp.gear.d)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class involute_gear_rack():

    """FreeCAD gear rack"""

    def __init__(self, obj):
        self.involute_rack = involute_rack()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyLength", "thickness", "gear_parameter", "thickness")
        obj.addProperty(
            "App::PropertyAngle", "alpha", "involute_parameter", "alpha")
        obj.addProperty("App::PropertyPythonObject", "rack", "test", "test")
        obj.rack = self.involute_rack
        obj.teeth = 15
        obj.module = '1. mm'
        obj.alpha = '20. deg'
        obj.height = '5. mm'
        obj.thickness = '5 mm'
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        fp.rack.m = fp.module.Value
        fp.rack.z = fp.teeth
        fp.rack.alpha = fp.alpha.Value * pi / 180.
        fp.rack.thickness = fp.thickness.Value
        fp.rack._update()
        pts = fp.rack.points()
        pol = Wire(makePolygon(map(fcvec, pts)))
        fp.Shape = Face(Wire(pol)).extrude(fcvec([0., 0., fp.height]))

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class cycloide_gear():

    """FreeCAD gear"""

    def __init__(self, obj):
        self.cycloide_tooth = cycloide_tooth()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "inner_diameter", "cycloid_parameter", "inner_diameter")
        obj.addProperty(
            "App::PropertyLength", "outer_diameter", "cycloid_parameter", "outer_diameter")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyFloat", "clearence", "gear_parameter", "clearence")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "gear_parameter", "number of points for spline")
        obj.addProperty("App::PropertyAngle", "beta", "gear_parameter", "beta")
        obj.addProperty(
            "App::PropertyLength", "backlash", "gear_parameter", "backlash in mm")
        obj.addProperty("App::PropertyPythonObject", "gear", "test", "test")
        obj.gear = self.cycloide_tooth
        obj.teeth = 15
        obj.module = '1. mm'
        obj.inner_diameter = '5 mm'
        obj.outer_diameter = '5 mm'
        obj.beta = '0. deg'
        obj.height = '5. mm'
        obj.clearence = 0.25
        obj.numpoints = 15
        obj.backlash = '0.00 mm'
        obj.Proxy = self

    def execute(self, fp):
        pass
        fp.gear.m = fp.module.Value
        fp.gear.z = fp.teeth
        fp.gear.z1 = fp.inner_diameter.Value
        fp.gear.z2 = fp.outer_diameter.Value
        fp.gear.clearence = fp.clearence
        fp.gear.backlash = fp.backlash.Value
        fp.gear._update()
        pts = fp.gear.points(num=fp.numpoints)
        wi = []
        for i in pts:
            out = BSplineCurve()
            out.interpolate(map(fcvec, i))
            wi.append(out)
        s = Wire(Shape(wi).Edges)
        wi = []
        for i in range(fp.gear.z):
            rot = App.Matrix()
            rot.rotateZ(-i * fp.gear.phipart)
            tooth_rot = s.transformGeometry(rot)
            if i != 0:
                pt_0 = wi[-1].Edges[-1].Vertexes[0].Point
                pt_1 = tooth_rot.Edges[0].Vertexes[-1].Point
                wi.append(Wire([Line(pt_0, pt_1).toShape()]))
            wi.append(tooth_rot)
        pt_0 = wi[-1].Edges[-1].Vertexes[0].Point
        pt_1 = wi[0].Edges[0].Vertexes[-1].Point
        wi.append(Wire([Line(pt_0, pt_1).toShape()]))
        wi = Wire(wi)
        if fp.beta == 0:
            sh = Face(wi)
            fp.Shape = sh.extrude(App.Vector(0, 0, fp.height.Value))
        else:
            fp.Shape = helicalextrusion(
                wi, fp.height.Value, fp.height.Value * tan(fp.beta.Value * pi / 180) * 2 / fp.gear.d)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class bevel_gear():

    """parameters:
        alpha:  pressureangle,   10-30°
        gamma:  cone angle,      0 < gamma < pi/4
    """

    def __init__(self, obj):
        self.bevel_tooth = bevel_tooth()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyAngle", "gamma", "involute_parameter", "gamma")
        obj.addProperty(
            "App::PropertyAngle", "alpha", "involute_parameter", "alpha")
        obj.addProperty("App::PropertyLength", "m", "gear_parameter", "m")
        obj.addProperty(
            "App::PropertyLength", "c", "gear_parameter", "clearence")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "gear_parameter", "number of points for spline")
        obj.addProperty(
            "App::PropertyLength", "backlash", "gear_parameter", "backlash in mm")
        obj.addProperty("App::PropertyPythonObject", "gear", "test", "test")
        obj.gear = self.bevel_tooth
        obj.m = '1. mm'
        obj.teeth = 15
        obj.alpha = '70. deg'
        obj.gamma = '45. deg'
        obj.height = '5. mm'
        obj.numpoints = 6
        obj.backlash = '0.00 mm'
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        fp.gear.z = fp.teeth
        fp.gear.alpha = fp.alpha.Value * pi / 180.
        fp.gear.gamma = fp.gamma.Value * pi / 180
        fp.gear.backlash = fp.backlash.Value
        fp.gear._update()
        pts = fp.gear.points(num=fp.numpoints)
        # w1 = self.createteeths(pts, fp.m.Value * fp.gear.z / 2 / tan(
        #     fp.gamma.Value * pi / 180) + fp.height.Value / 2, fp.gear.z)
        # w2 = self.createteeths(pts, fp.m.Value * fp.gear.z / 2 / tan(
        #     fp.gamma.Value * pi / 180) - fp.height.Value / 2, fp.gear.z)
        fpts = [map(fcvec, i) for i in pts]
        l = []
        for pt in fpts:
            b = BSplineCurve()
            b.interpolate(pt)
            l.append(b)
        fp.Shape = self.create_tooth()

    def create_tooth(self):
        w = []
        scal1 = self.obj.m.Value * self.obj.gear.z / 2 / tan(
            self.obj.gamma.Value * pi / 180) - self.obj.height.Value / 2
        scal2 = self.obj.m.Value * self.obj.gear.z / 2 / tan(
            self.obj.gamma.Value * pi / 180) + self.obj.height.Value / 2
        s = [scal1, scal2]
        pts = self.obj.gear.points(num=self.obj.numpoints)
        for pos in s:
            w1 = []
            scale = lambda x: fcvec(x * pos)
            for i in pts:
                i_scale = map(scale, i)
                w1.append(i_scale)
            w.append(w1)
        surfs = []
        w_t = zip(*w)
        for i in w_t:
            b = BSplineSurface()
            b.interpolate(i)
            surfs.append(b)
        return Shape(surfs)

    def createteeths(self, pts, pos, teeth):
        w1 = []
        for i in pts:
            scale = lambda x: x * pos
            i_scale = map(scale, i)
            out = BSplineCurve()
            out.interpolate(map(fcvec, i_scale))
            w1.append(out)
        s = Wire(Shape(w1).Edges)
        wi = []
        for i in range(teeth):
            rot = App.Matrix()
            rot.rotateZ(2 * i * pi / teeth)
            tooth_rot = s.transformGeometry(rot)
            if i != 0:
                pt_0 = wi[-1].Edges[-1].Vertexes[0].Point
                pt_1 = tooth_rot.Edges[0].Vertexes[-1].Point
                wi.append(Wire([Line(pt_0, pt_1).toShape()]))
            wi.append(tooth_rot)
        pt_0 = wi[-1].Edges[-1].Vertexes[0].Point
        pt_1 = wi[0].Edges[0].Vertexes[-1].Point
        wi.append(Wire([Line(pt_0, pt_1).toShape()]))
        return(Wire(wi))

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def helicalextrusion(wire, height, angle):
    face_a = Face(wire)
    face_b = face_a.copy()
    face_transform = App.Matrix()
    face_transform.rotateZ(angle)
    face_transform.move(App.Vector(0, 0, height))
    face_b . transformShape(face_transform)
    step = 2 + int(angle / pi * 4)
    angleinc = angle / (step - 1)
    zinc = height / (step - 1)
    spine = makePolygon([(0, 0, i * zinc) for i in range(step)])
    auxspine = makePolygon(
        [
            (cos(i * angleinc),
             sin(i * angleinc),
             i * height / (step - 1))for i in range(step)
        ])
    faces = [face_a, face_b]
    pipeshell = BRepOffsetAPI.MakePipeShell(spine)
    pipeshell.setSpineSupport(spine)
    pipeshell.add(wire)
    pipeshell.setAuxiliarySpine(auxspine, True, False)
    assert(pipeshell.isReady())
    pipeshell.build()
    faces.extend(pipeshell.shape().Faces)

    fullshell = Shell(faces)
    solid = Solid(fullshell)
    if solid.Volume < 0:
        solid.reverse()
    assert(solid.Volume >= 0)
    return(solid)