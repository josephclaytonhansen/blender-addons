from mathutils import Euler, Vector
import bpy

# ----------------------- Weight calculation functions ----------------------- #


def getDistances(links, currentLightRotation, currentLightPosition):
    """
    Prerequisite for calculating weights;
    Finds the angular distance between the current light rotation
    and each of the stored light rotations.
    """
    distances = []
    current_quat = currentLightRotation.to_quaternion()

    for corr in links:
        corr_euler = corr.light_rotation
        corr_quat = corr_euler.to_quaternion()
        dist = current_quat.rotation_difference(corr_quat).angle
        
        pos_dist = (Vector(currentLightPosition) - Vector(corr.light_position)).length
        average_dist = (dist + pos_dist) / 2.0
        distances.append(average_dist)

    return distances


def getWeights(distances):
    """
    Calculates normalized inverse distance weights.
    A smaller distance results in a larger weight.
    All weights are positive and sum to 1.0.
    """
    if not distances:
        return []

    weights = []
    total_weight = 0.0
    epsilon = 1e-6

    for d in distances:
        weight = 1.0 / (d + epsilon)
        weights.append(weight)
        total_weight += weight

    if total_weight > 0:
        for i in range(len(weights)):
            weights[i] /= total_weight
    
    addon_prefs = bpy.context.preferences.addons["shading-rig-and-cel-character-tools"].preferences
    if addon_prefs.debug_mode:
        print(weights)

    return weights


def calculateWeightedEmptyPosition(links, currentLightRotation, currentLightPosition):
    """
    Given a list of light rotations -> empty positions and a current light
    rotation, interpolates the empty position.
    """
    if not links:
        return [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]
    
    if len(links) == 1:
        return list(links[0].empty_position), list(links[0].empty_scale), list(links[0].empty_rotation)
    
    distances = getDistances(links, currentLightRotation, currentLightPosition)
    weights = getWeights(distances)
    
    weighted_position = Vector((0.0, 0.0, 0.0))
    weighted_scale = Vector((0.0, 0.0, 0.0))
    weighted_rotation = Vector((0.0, 0.0, 0.0))
    
    for i, corr in enumerate(links):
        weight = weights[i]
        weighted_position += Vector(corr.empty_position) * weight
        weighted_scale += Vector(corr.empty_scale) * weight
        weighted_rotation += Vector(corr.empty_rotation) * weight
    
    return list(weighted_position), list(weighted_scale), list(weighted_rotation)
