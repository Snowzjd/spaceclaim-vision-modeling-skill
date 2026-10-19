def operation(p):
    # The caller must discard previously cached topology references.
    bodies = current_bodies()
    return {"bodies": bodies, "faces": [face for body in bodies for face in list(body.Faces)], "edges": [edge for body in bodies for edge in list(body.Edges)]}
